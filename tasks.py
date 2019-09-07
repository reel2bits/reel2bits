from __future__ import print_function

from models import db, Sound, User
from flask_mail import Message
from flask import render_template, url_for
from app import mail, create_app, make_celery
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
from activitypub.vars import HEADERS, Box
from controllers.sound import bp_sound
import smtplib
from utils import add_log, add_user_log

# TRANSCODING

# Make some gloubiboulga about Flask app context
app = create_app(register_blueprints=False)
celery = make_celery(app)


def federate_new_sound(sound: Sound) -> int:
    if not current_app.config["AP_ENABLED"]:
        return None

    actor = sound.user.actor[0]
    cc = [actor.followers_url]
    href = url_for("get_uploads_stuff", thing="sounds", stuff=sound.path_sound())

    raw_audio = dict(
        attributedTo=actor.url,
        cc=list(set(cc)),
        to=[ap.AS_PUBLIC],
        inReplyTo=None,
        name=sound.title,
        content=sound.description,
        mediaType="text/plain",
        url={"type": "Link", "href": href, "mediaType": "audio/mp3"},
    )

    audio = ap.Audio(**raw_audio)
    create = audio.build_create()
    # Post to outbox and save Activity id into Sound relation
    activity_id = post_to_outbox(create)
    activity = Activity.query.filter(Activity.box == Box.OUTBOX.value, Activity.url == activity_id).first()
    # TODO FIXME: not sure about all that ID crap
    return activity.id


def federate_delete_sound(sound: Sound) -> None:
    if not current_app.config["AP_ENABLED"]:
        return

    actor = sound.user.actor[0].to_dict()
    # Get activity
    # Create delete
    # Somehow we needs to add /activity here
    # FIXME do that better
    delete = ap.Delete(
        actor=actor, object=ap.Tombstone(id=sound.activity.payload["id"] + "/activity").to_dict(embed=True)
    )
    # Federate
    post_to_outbox(delete)


@celery.task(bind=True, max_retries=3)
def upload_workflow(self, sound_id):
    print("UPLOAD WORKFLOW started")

    sound = Sound.query.get(sound_id)
    if not sound:
        print("- Cant find sound ID {id} in database".format(id=sound_id))
        return

    errors = None

    print("METADATAS started")
    metadatas = work_metadatas(sound_id)
    print("METADATAS finished")

    if not metadatas:
        # cannot process further
        errors = True
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

    # Federate if public and AP enabled
    if current_app.config["AP_ENABLED"] and not errors:
        if not sound.private:
            print("UPLOAD WORKFLOW federating sound")
            # Federate only if sound is public
            sound.activity_id = federate_new_sound(sound)
            db.session.commit()

    app.register_blueprint(bp_sound)

    msg = Message(
        subject="Song processing finished",
        recipients=[sound.user.email],
        sender=current_app.config["MAIL_DEFAULT_SENDER"],
    )
    msg.body = render_template("email/song_processed.txt", sound=sound)
    msg.html = render_template("email/song_processed.html", sound=sound)
    err = None
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
    except smtplib.SMTPAuthenticationError as e:
        print(f"Error sending mail: {e}")
        err = e
    except smtplib.SMTPRecipientsRefused as e:
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

        current_app.logger.info(f"finish_post_to_outbox {activity}")

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


def post_to_outbox(activity: ap.BaseActivity) -> str:
    current_app.logger.debug(f"post_to_outbox {activity}")

    if activity.has_type(ap.CREATE_TYPES):
        activity = activity.build_create()

    backend = ap.get_backend()

    # Assign a random ID
    obj_id = backend.random_object_id()
    activity.set_id(backend.activity_url(obj_id), obj_id)

    backend.save(Box.OUTBOX, activity)

    finish_post_to_outbox.delay(activity.id)
    return activity.id


def send_update_profile(user: User) -> None:
    if not current_app.config["AP_ENABLED"]:
        return  # not federating if not enabled

    # FIXME: not sure at all about that
    actor = user.actor[0]
    raw_update = dict(
        to=[follower.actor.url for follower in actor.followers], actor=actor.to_dict(), object=actor.to_dict()
    )
    current_app.logger.debug(f"recipients: {raw_update['to']}")
    update = ap.Update(**raw_update)
    post_to_outbox(update)


def send_update_sound(sound: Sound) -> None:
    if not current_app.config["AP_ENABLED"]:
        return  # not federating if not enabled

    # FIXME: not sure at all about that
    # Should not even work
    actor = sound.user.actor[0]

    # Fetch object and update fields
    object = sound.activity.payload["object"]
    object["name"] = sound.title
    object["content"] = sound.description

    raw_update = dict(to=[follower.actor.url for follower in actor.followers], actor=actor.to_dict(), object=object)
    current_app.logger.debug(f"recipients: {raw_update['to']}")
    update = ap.Update(**raw_update)
    post_to_outbox(update)
