from __future__ import print_function

from models import db, Sound, User, Config, SoundTag
from flask_mail import Message
from flask import render_template, url_for
from app import create_app, make_celery
from transcoding_utils import work_transcode, work_metadatas
from little_boxes import activitypub as ap
from little_boxes.linked_data_sig import generate_signature
from little_boxes.httpsig import HTTPSigAuth
from flask import current_app
import requests
import json
from requests.exceptions import HTTPError
from little_boxes.errors import ActivityGoneError
from little_boxes.errors import ActivityNotFoundError
from little_boxes.errors import NotAnActivityError
from little_boxes.key import Key
from models import Activity, Actor
from activitypub.vars import HEADERS, Box, DEFAULT_CTX
import smtplib
from utils.various import add_log, add_user_log

# TRANSCODING

# Make some gloubiboulga about Flask app context
app = create_app(register_blueprints=False)
# Special case where we need to force SERVER_NAME: Celery
app.config["SERVER_NAME"] = app.config["AP_DOMAIN"]
celery = make_celery(app)


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    pass


def federate_new_sound(sound: Sound) -> int:
    actor = sound.user.actor[0]
    cc = [actor.followers_url]
    url_orig = url_for("get_uploads_stuff", thing="sounds", stuff=sound.path_sound(orig=True), _external=True)
    # url_transcode = url_for("get_uploads_stuff", thing="sounds", stuff=sound.path_sound(orig=False), _external=True)

    # if sound.path_artwork():
    #     url_artwork = url_for("get_uploads_stuff", thing="artwork_sounds", stuff=sound.path_artwork(), _external=True)
    # else:
    #     url_artwork = None

    raw_audio = dict(
        attributedTo=actor.url,
        cc=list(set(cc)),
        to=[ap.AS_PUBLIC],
        inReplyTo=None,
        name=sound.title,
        content=sound.description,
        mediaType="text/plain",
        url={"type": "Link", "href": url_orig, "mediaType": "audio/mp3"},
        # custom items
        # tags=[t.name for t in sound.tags],
        # genre=sound.genre,
        # licence=sound.licence_info(),
        # artwork=url_artwork,
        # transcoded=sound.transcode_needed,
        # transcode_url=(url_transcode if sound.transcode_needed else None),
    )
    raw_audio["@context"] = DEFAULT_CTX

    # FIXME(dashie): apparently the @context is ignored by the Audio() or build_create()

    audio = ap.Audio(**raw_audio)
    print("BUILD CREATE FEDERATE_NEW_SOUND")
    create = audio.build_create()
    # Post to outbox and save Activity id into Sound relation
    activity_id = post_to_outbox(create)
    activity = Activity.query.filter(Activity.box == Box.OUTBOX.value, Activity.url == activity_id).first()
    # TODO FIXME: not sure about all that ID crap
    return activity.id


def federate_delete_sound(sound: Sound) -> None:
    if not current_app.config["AP_ENABLED"]:
        return

    # TODO FIXME: to who is the delete sent ?

    actor = sound.user.actor[0].to_dict()
    # Get activity
    # Create delete
    # Somehow we needs to add /activity here
    # FIXME do that better
    if not sound.activity:
        # track never federated
        return
    delete = ap.Delete(
        actor=actor, object=ap.Tombstone(id=sound.activity.payload["id"] + "/activity").to_dict(embed=True)
    )
    # Federate
    post_to_outbox(delete)


def federate_delete_actor(actor: Actor) -> None:
    # TODO FIXME: to who is the delete sent ?

    actor = actor.to_dict()
    # Create delete
    # No need for '/activity' here ?
    # FIXME do that better
    delete = ap.Delete(actor=actor, object=ap.Tombstone(id=actor["id"]).to_dict(embed=True))
    # Federate
    post_to_outbox(delete)


def create_sound_for_remote_track(activity: Activity) -> int:
    sound = Sound()
    sound.title = activity.payload.get("object", {}).get("name", None)
    sound.description = activity.payload.get("object", {}).get("content", None)
    sound.private = False
    sound.transcode_needed = activity.payload.get("object", {}).get("transcoded", False)
    if sound.transcode_needed:
        sound.remote_uri = activity.payload.get("object", {}).get("transcode_url", None)
    else:
        sound.remote_uri = activity.payload.get("object", {}).get("url", {}).get("href", None)
    sound.transcode_state = 0

    # Get user through actor
    sound.user_id = activity.actor.user.id
    sound.activity_id = activity.id
    # custom from AP
    sound.artwork_filename = activity.payload.get("object", {}).get("artwork", None)
    sound.genre = activity.payload.get("object", {}).get("genre", None)
    sound.licence = activity.payload.get("object", {}).get("licence", {}).get("id", 0)

    if not sound.filename:
        return None  # reject if no file available

    # Tags handling. Since it's a new track, no need to do magic tags recalculation.
    tags = [t.strip() for t in activity.payload.get("object", {}).get("tags", [])]
    for tag in tags:
        dbt = SoundTag.query.filter(SoundTag.name == tag).first()
        if not dbt:
            dbt = SoundTag(name=tag)
            db.session.add(dbt)
        sound.tags.append(dbt)

    db.session.add(sound)
    db.session.commit()
    return sound.id


@celery.task(bind=True, max_retries=3)
def fetch_remote_track(self, sound: Sound):
    print(f"Started fetching remote track {sound.id}")
    if not sound.remote_uri.startswith("http://") or not sound.remote_uri.startswith("https://"):
        print(f"ERROR: cannot fetch {sound.remote_uri!r} because of invalid protocol")
        return False

    print(f"Finished fetching remote track {sound.id}")


@celery.task(bind=True, max_retries=3)
def upload_workflow(self, sound_id):
    print("UPLOAD WORKFLOW started")

    sound = Sound.query.get(sound_id)
    if not sound:
        print("- Cant find sound ID {id} in database".format(id=sound_id))
        return

    # First, if the sound isn't local, we need to fetch it
    if not sound.activity.local:
        fetched = fetch_remote_track(sound)
        if not fetched:
            print("UPLOAD WORKFLOW had errors")
            add_log("global", "ERROR", f"Error fetching remote track {sound.id}")
            return

    print("METADATAS started")
    metadatas = work_metadatas(sound_id)
    print("METADATAS finished")

    if not metadatas:
        # cannot process further
        sound.transcode_state = Sound.TRANSCODE_ERROR
        db.session.commit()
        print("UPLOAD WORKFLOW had errors")
        add_log("global", "ERROR", f"Error processing track {sound.id}")
        add_user_log(sound.id, sound.user.id, "sounds", "error", "An error occured while processing your track")
        return

    if metadatas:
        print("TRANSCODE started")
        work_transcode(sound_id)
        print("TRANSCODE finished")

    # Federate if public
    if not sound.private:
        print("UPLOAD WORKFLOW federating sound")
        # Federate only if sound is public
        sound.activity_id = federate_new_sound(sound)
        db.session.commit()

    track_url = f"https://{current_app.config['AP_DOMAIN']}/{sound.user.name}/track/{sound.slug}"

    msg = Message(
        subject="Song processing finished",
        recipients=[sound.user.email],
        sender=current_app.config["MAIL_DEFAULT_SENDER"],
    )

    _config = Config.query.first()
    if not _config:
        print("ERROR: cannot get instance Config from database")
    instance = {"name": None, "url": None}
    if _config:
        instance["name"] = _config.app_name
    instance["url"] = current_app.config["REEL2BITS_URL"]
    msg.body = render_template("email/song_processed.txt", sound=sound, track_url=track_url, instance=instance)
    msg.html = render_template("email/song_processed.html", sound=sound, track_url=track_url, instance=instance)
    err = None
    mail = current_app.extensions.get("mail")
    if not mail:
        err = "mail extension is none"
    else:
        try:
            mail.send(msg)
        except ConnectionRefusedError as e:
            # TODO: do something about that maybe
            print(f"Error sending mail: {e}")
            err = e
        except smtplib.SMTPRecipientsRefused as e:
            print(f"Error sending mail: {e}")
            err = e
        except smtplib.SMTPException as e:
            print(f"Error sending mail: {e}")
            err = e
    if err:
        add_log("global", "ERROR", f"Error sending email for track {sound.id}: {err}")
        add_user_log(sound.id, sound.user.id, "sounds", "error", "An error occured while sending email")

    print("UPLOAD WORKFLOW finished")


# ACTIVITYPUB


@celery.task(bind=True, max_retries=3)
def process_new_activity(self, iri: str) -> None:
    try:
        activity = ap.fetch_remote_activity(iri)
        current_app.logger.info(f"activity={activity!r}")

        actor = activity.get_actor()
        id = actor.id
        current_app.logger.debug(f"process_new_activity actor {id}")

        # Is the activity expected?
        # following = ap.get_backend().following()
        should_forward = False
        should_delete = False

        tag_stream = False
        if activity.has_type(ap.ActivityType.ANNOUNCE):
            try:
                activity.get_object()
                tag_stream = True
            except NotAnActivityError:
                # Most likely on OStatus notice
                tag_stream = False
                should_delete = True
            except (ActivityGoneError, ActivityNotFoundError):
                # The announced activity is deleted/gone, drop it
                should_delete = True

        elif activity.has_type(ap.ActivityType.CREATE):
            note = activity.get_object()
            # Make the note part of the stream if it's not a reply,
            # or if it's a local reply
            if not note.inReplyTo or note.inReplyTo.startswith(id):
                tag_stream = True

            if note.inReplyTo:
                try:
                    reply = ap.fetch_remote_activity(note.inReplyTo)
                    if (reply.id.startswith(id) or reply.has_mention(id)) and activity.is_public():
                        # The reply is public "local reply", forward the
                        # reply (i.e. the original activity) to the
                        # original recipients
                        should_forward = True
                except NotAnActivityError:
                    # Most likely a reply to an OStatus notce
                    should_delete = True

            # (partial) Ghost replies handling
            # [X] This is the first time the server has seen this Activity.
            should_forward = False
            local_followers = id + "/followers"  # FIXME URL might be different
            for field in ["to", "cc"]:
                if field in activity._data:
                    if local_followers in activity._data[field]:
                        # [X] The values of to, cc, and/or audience contain a
                        #  Collection owned by the server.
                        should_forward = True

            # [X] The values of inReplyTo, object, target and/or tag are
            # objects owned by the server
            if not (note.inReplyTo and note.inReplyTo.startswith(id)):
                should_forward = False

        elif activity.has_type(ap.ActivityType.DELETE):
            note = Activity.query.filter(Activity.id == activity.get_object().id).first()
            if note and note["meta"].get("forwarded", False):
                # If the activity was originally forwarded, forward the
                # delete too
                should_forward = True

        elif activity.has_type(ap.ActivityType.LIKE):
            base_url = current_app.config["AP_DOMAIN"]
            if not activity.get_object_id().startswith(base_url):
                # We only want to keep a like if it's a like for a local
                # activity
                # (Pleroma relay the likes it received, we don't want to
                # store them)
                should_delete = True

        if should_forward:
            current_app.logger.info(f"will forward {activity!r} to followers")
            forward_activity.delay(activity.id)

        if should_delete:
            current_app.logger.info(f"will soft delete {activity!r}")

            current_app.logger.info(f"{activity.id} tag_stream={tag_stream}")
        # Update Activity:
        #    {"remote_id": activity.id},
        #        "$set": {
        #           "meta.stream": tag_stream,
        #           "meta.forwarded": should_forward,
        #           "meta.deleted": should_delete,

        current_app.logger.info(f"new activity {activity.id} processed")

    except (ActivityGoneError, ActivityNotFoundError):
        current_app.logger.exception(f"failed to process new activity" f" {iri}")
    except Exception as err:  # noqa: F841
        current_app.logger.exception(f"failed to process new activity" f" {iri}")


@celery.task(bind=True, max_retries=3)
def finish_inbox_processing(self, iri: str) -> None:
    try:
        backend = ap.get_backend()

        activity = ap.fetch_remote_activity(iri)
        current_app.logger.info(f"activity={activity!r}")

        actor = activity.get_actor()
        id = activity.get_object_id()
        current_app.logger.debug(f"finish_inbox_processing actor {actor}")

        if activity.has_type(ap.ActivityType.DELETE):
            backend.inbox_delete(actor, activity)
        elif activity.has_type(ap.ActivityType.UPDATE):
            backend.inbox_update(actor, activity)
        elif activity.has_type(ap.ActivityType.CREATE):
            backend.inbox_create(actor, activity)
        elif activity.has_type(ap.ActivityType.ANNOUNCE):
            backend.inbox_announce(actor, activity)
        elif activity.has_type(ap.ActivityType.LIKE):
            backend.inbox_like(actor, activity)
        elif activity.has_type(ap.ActivityType.FOLLOW):
            # Reply to a Follow with an Accept
            accept = ap.Accept(actor=id, object=activity.to_dict(embed=True))
            post_to_outbox(accept)
            backend.new_follower(activity, activity.get_actor(), activity.get_object())
        elif activity.has_type(ap.ActivityType.ACCEPT):
            obj = activity.get_object()
            # FIXME: probably other types to ACCEPT the Activity
            if obj.has_type(ap.ActivityType.FOLLOW):
                # Accept new follower
                backend.new_following(activity, obj)
        elif activity.has_type(ap.ActivityType.UNDO):
            obj = activity.get_object()
            if obj.has_type(ap.ActivityType.LIKE):
                backend.inbox_undo_like(actor, obj)
            elif obj.has_type(ap.ActivityType.ANNOUNCE):
                backend.inbox_undo_announce(actor, obj)
            elif obj.has_type(ap.ActivityType.FOLLOW):
                backend.undo_new_follower(actor, obj)
    except (ActivityGoneError, ActivityNotFoundError, NotAnActivityError):
        current_app.logger.exception(f"no retry")
    except Exception as err:  # noqa: F841
        current_app.logger.exception(f"failed to cache attachments for" f" {iri}")


@celery.task(bind=True, max_retries=3)
def finish_post_to_outbox(self, iri: str) -> None:
    try:
        activity = ap.fetch_remote_activity(iri)
        backend = ap.get_backend()

        current_app.logger.info(f"finish_post_to_outbox {activity!r}")

        recipients = activity.recipients()

        actor = activity.get_actor()
        current_app.logger.debug(f"finish_post_to_outbox actor {actor!r}")

        if activity.has_type(ap.ActivityType.DELETE):
            backend.outbox_delete(actor, activity)
        elif activity.has_type(ap.ActivityType.UPDATE):
            backend.outbox_update(actor, activity)
        elif activity.has_type(ap.ActivityType.CREATE):
            backend.outbox_create(actor, activity)
        elif activity.has_type(ap.ActivityType.ANNOUNCE):
            backend.outbox_announce(actor, activity)
        elif activity.has_type(ap.ActivityType.LIKE):
            backend.outbox_like(actor, activity)
        elif activity.has_type(ap.ActivityType.UNDO):
            obj = activity.get_object()
            if obj.has_type(ap.ActivityType.LIKE):
                backend.outbox_undo_like(actor, obj)
            elif obj.has_type(ap.ActivityType.ANNOUNCE):
                backend.outbox_undo_announce(actor, obj)
            elif obj.has_type(ap.ActivityType.FOLLOW):
                backend.undo_new_following(actor, obj)

        current_app.logger.info(f"recipients={recipients}")
        activity = ap.clean_activity(activity.to_dict())

        payload = json.dumps(activity)
        for recp in recipients:
            current_app.logger.debug(f"posting to {recp}")
            post_to_remote_inbox.delay(payload, recp)
    except (ActivityGoneError, ActivityNotFoundError):
        current_app.logger.exception(f"no retry")
    except Exception as err:  # noqa: F841
        current_app.logger.exception(f"failed to post " f"to remote inbox for {iri}")


@celery.task(bind=True, max_retries=3)
def post_to_remote_inbox(self, payload: str, to: str) -> None:
    if not current_app.config["AP_ENABLED"]:
        return  # not federating if not enabled

    current_app.logger.debug(f"post_to_remote_inbox {payload}")

    ap_actor = json.loads(payload)["actor"]
    actor = Actor.query.filter(Actor.url == ap_actor).first()
    if not actor:
        current_app.logger.exception("no actor found")
        return

    key = Key(owner=actor.url)
    key.load(actor.private_key)

    signature_auth = HTTPSigAuth(key)

    # current_app.logger.debug(f"key=={key.__dict__}")

    try:
        current_app.logger.info("payload=%s", payload)
        current_app.logger.info("generating sig")
        signed_payload = json.loads(payload)

        backend = ap.get_backend()

        # Don't overwrite the signature if we're forwarding an activity
        if "signature" not in signed_payload:
            generate_signature(signed_payload, key)

        current_app.logger.info("to=%s", to)
        resp = requests.post(
            to,
            data=json.dumps(signed_payload),
            auth=signature_auth,
            headers={"Content-Type": HEADERS[1], "Accept": HEADERS[1], "User-Agent": backend.user_agent()},
        )
        current_app.logger.info("resp=%s", resp)
        current_app.logger.info("resp_body=%s", resp.text)
        resp.raise_for_status()
    except HTTPError as err:
        current_app.logger.exception("request failed")
        if 400 >= err.response.status_code >= 499:
            current_app.logger.info("client error, no retry")
    return


@celery.task(bind=True, max_retries=3)
def forward_activity(self, iri: str) -> None:
    if not current_app.config["AP_ENABLED"]:
        return  # not federating if not enabled

    try:
        activity = ap.fetch_remote_activity(iri)
        backend = ap.get_backend()
        recipients = backend.followers_as_recipients()
        current_app.logger.debug(f"Forwarding {activity!r} to {recipients}")
        activity = ap.clean_activity(activity.to_dict())
        for recp in recipients:
            current_app.logger.debug(f"forwarding {activity!r} to {recp}")
            payload = json.dumps(activity)
            post_to_remote_inbox.delay(payload, recp)

    except Exception as err:  # noqa: F841
        current_app.logger.exception(f"failed to cache attachments for {iri}")


# We received an activity, now we have to process it in two steps
def post_to_inbox(activity: ap.BaseActivity) -> None:
    # actor = activity.get_actor()
    backend = ap.get_backend()

    # TODO: drop if emitter is blocked
    # backend.outbox_is_blocked(target actor, actor.id)

    # TODO: drop if duplicate
    # backend.inbox_check_duplicate(actor, activity.id)

    backend.save(Box.INBOX, activity)

    process_new_activity.delay(activity.id)

    finish_inbox_processing.delay(activity.id)


# If AP_ENABLED=False we still runs this bit to save the activites in the database
# Except we don't run the finish part which broadcast the activity since not enabled
def post_to_outbox(activity: ap.BaseActivity) -> str:
    current_app.logger.debug(f"post_to_outbox {activity!r}")

    if activity.has_type(ap.CREATE_TYPES):
        print("BUILD CREATE POST TO OUTBOX")
        activity = activity.build_create()

    backend = ap.get_backend()

    # Assign a random ID
    obj_id = backend.random_object_id()
    activity.set_id(backend.activity_url(obj_id), obj_id)

    backend.save(Box.OUTBOX, activity)

    # Broadcast only if AP is enabled
    if current_app.config["AP_ENABLED"]:
        finish_post_to_outbox.delay(activity.id)
    return activity.id


def send_update_profile(user: User) -> None:
    # FIXME: not sure at all about that
    actor = user.actor[0]
    raw_update = dict(
        to=[follower.actor.url for follower in actor.followers], actor=actor.to_dict(), object=actor.to_dict()
    )
    current_app.logger.debug(f"recipients: {raw_update['to']}")
    update = ap.Update(**raw_update)
    post_to_outbox(update)


def send_update_sound(sound: Sound) -> None:
    # FIXME: not sure at all about that
    # Should not even work
    actor = sound.user.actor[0]

    if sound.path_artwork():
        url_artwork = url_for("get_uploads_stuff", thing="artwork_sounds", stuff=sound.path_artwork(), _external=True)
    else:
        url_artwork = None

    # Fetch object and update fields
    object = sound.activity.payload["object"]
    object["name"] = sound.title
    object["content"] = sound.description
    # custom things that can change
    object["tags"] = [t.name for t in sound.tags]
    object["genre"] = sound.genre
    object["licence"] = sound.licence_info()
    object["artwork"] = url_artwork

    # if no followers, to=[], maybe it should includes the #Public as is the object already including it ?
    raw_update = dict(to=[follower.actor.url for follower in actor.followers], actor=actor.to_dict(), object=object)
    raw_update["@context"] = DEFAULT_CTX
    current_app.logger.debug(f"recipients: {raw_update['to']}")
    update = ap.Update(**raw_update)
    post_to_outbox(update)
