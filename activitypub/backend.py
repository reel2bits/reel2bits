from little_boxes import activitypub as ap
from little_boxes.linked_data_sig import generate_signature
from little_boxes.httpsig import HTTPSigAuth
from flask import current_app, g
import requests
from enum import Enum
import json
from requests.exceptions import HTTPError
from little_boxes.errors import ActivityGoneError
from little_boxes.errors import ActivityNotFoundError
from little_boxes.errors import NotAnActivityError
from little_boxes.key import Key
from models import db, Activity, create_remote_actor, Actor, User
from urllib.parse import urlparse


class Box(Enum):
    INBOX = "inbox"
    OUTBOX = "outbox"
    REPLIES = "replies"


HEADERS = [
    "application/activity+json",
    "application/ld+json;profile=https://www.w3.org/ns/activitystreams",
    'application/ld+json; profile="https://www.w3.org/ns/activitystreams"',
    "application/ld+json",
]


class Reel2BitsBackend(ap.Backend):
    def debug_mode(self) -> bool:
        return current_app.config["DEBUG"]

    def user_agent(self) -> str:
        url = current_app.config["BASE_URL"]
        return f"{requests.utils.default_user_agent()} " f"(reel2bits/{g.cfg['REEL2BITS_VERSION_VER']}; +{url})"

    def base_url(self):
        return current_app.config["BASE_URL"]

    def activity_url(self, obj_id: str):
        return f"{self.base_url()}/outbox/{obj_id}"

    def note_url(self, obj_id: str):
        return f"{self.base_url()}/note/{obj_id}"

    def new_follower(self, activity: ap.BaseActivity, as_actor: ap.Person, follow: ap.Follow) -> None:
        current_app.logger.info("new follower")

        db_actor = Actor.query.filter(Actor.url == as_actor.id).first()
        db_follow = Actor.query.filter(Actor.url == follow.id).first()
        if not db_actor:
            current_app.logger.error(f"cannot find actor {as_actor!r}")
            return
        if not db_follow:
            current_app.logger.error(f"cannot find follow {follow!r}")
            return

        current_app.logger.info(f"{db_actor.name} wanted " f"to follow {db_follow.name}")

        db_actor.follow(activity.id, db_follow)
        db.session.commit()
        current_app.logger.info("new follower saved")

    def new_following(self, activity: ap.BaseActivity, obj: ap.BaseActivity) -> None:
        current_app.logger.info("new following")

        ap_from = obj.get_actor()  # Who initiated the follow
        ap_to = activity.get_actor()  # who to be followed

        db_from = Actor.query.filter(Actor.url == ap_from.id).first()
        db_to = Actor.query.filter(Actor.url == ap_to.id).first()
        if not db_from:
            current_app.logger.error(f"cannot find actor {ap_from!r}")
            return
        if not db_to:
            current_app.logger.error(f"cannot find follow {ap_to!r}")
            return

        current_app.logger.info(f"{db_from.name} wanted to follow {db_to.name}")

        # FIXME: may be the reverse, db_follow follow db_actor
        db_from.follow(activity.id, db_to)
        db.session.commit()
        current_app.logger.info("new following saved")

    def undo_new_follower(self, as_actor: ap.Person, object: ap.Follow) -> None:
        current_app.logger.info("undo follower")
        current_app.logger.debug(f"{as_actor!r} unfollow-undoed {object!r}")
        # An unfollow is in fact "Undo an Activity"
        # ActivityPub is trash.

        undo_activity = object.id

        # fetch the activity
        activity = Activity.query.filter(Activity.url == undo_activity).first()
        if not activity:
            current_app.logger.error(f"cannot find activity" f" to undo: {undo_activity}")
            return

        # Parse the activity
        ap_activity = ap.parse_activity(activity.payload)
        if not ap_activity:
            current_app.logger.error(f"cannot parse undo follower activity")
            return

        actor = ap_activity.get_actor()
        follow = ap_activity.get_object()

        db_actor = Actor.query.filter(Actor.url == actor.id).first()
        db_follow = Actor.query.filter(Actor.url == follow.id).first()
        if not db_actor:
            current_app.logger.error(f"cannot find actor {actor!r}")
            return
        if not db_follow:
            current_app.logger.error(f"cannot find follow {follow!r}")
            return

        db_actor.unfollow(db_follow)
        db.session.commit()
        current_app.logger.info("undo follower saved")

    def undo_new_following(self, as_actor: ap.Person, object: ap.Follow) -> None:
        current_app.logger.info("undo following")

        actor_me = object.get_actor()

        current_app.logger.debug(f"{actor_me!r} unfollowing-undoed {object!r}")
        # An unfollowing is in fact "Undo an Activity"
        # ActivityPub is trash.

        follow_activity = Activity.query.filter(Activity.url == object.id).first()
        if not follow_activity:
            current_app.logger.error(f"cannot find activity {object}")
            return

        activity = ap.parse_activity(payload=follow_activity.payload)

        ap_actor_me = follow_activity.actor
        ap_actor_target = activity.get_object_id()

        db_actor = Actor.query.filter(Actor.id == ap_actor_me).first()
        db_follow = Actor.query.filter(Actor.url == ap_actor_target).first()
        if not db_actor:
            current_app.logger.error(f"cannot find actor {ap_actor_me!r}")
            return
        if not db_follow:
            current_app.logger.error(f"cannot find follow {ap_actor_target!r}")
            return

        # FIXME: may be the reverse, db_follow unfollow db_actor
        db_actor.unfollow(db_follow)
        db.session.commit()

        current_app.logger.info("undo following saved")

    def save(self, box: Box, activity: ap.BaseActivity) -> None:
        """Save an Activity in database"""

        current_app.logger.info(f"asked to save an activity {activity!r}")

        # Save remote Actor
        ap_actor = activity.get_actor()
        domain = urlparse(ap_actor.id)
        current_app.logger.debug(f"actor.id=={ap_actor.__dict__}")

        current_app.logger.debug(f"actor domain {domain.netloc} and " f"name {ap_actor.preferredUsername}")

        actor = Actor.query.filter(Actor.domain == domain.netloc, Actor.name == ap_actor.preferredUsername).first()

        # FIXME TODO: check if it still works with unknown remote actor
        if not actor:
            current_app.logger.debug(f"cannot find actor")
            actor = Actor.query.filter(Actor.url == ap_actor.id).first()
            if not actor:
                current_app.logger.debug(f"actor {ap_actor.id} not found")
                actor = create_remote_actor(ap_actor)
                db.session.add(actor)
                current_app.logger.debug("created one in DB")
            else:
                current_app.logger.debug(f"got local one {actor.url}")
        else:
            current_app.logger.debug(f"got remote one {actor.url}")

        # Save Activity
        act = Activity()
        act.payload = activity.to_dict()
        act.url = activity.id
        act.type = activity.type
        act.box = box.value

        # Activity is local only if the url starts like BASE_URL
        base_url = current_app.config["BASE_URL"]
        act.local = activity.id.startswith(base_url)

        act.actor = actor.id

        db.session.add(act)

        db.session.commit()

    def outbox_update(self, as_actor: ap.Person, activity: ap.BaseActivity):
        current_app.logger.debug(f"outbox_update {activity!r} as {as_actor!r}")


# We received an activity, now we have to process it in two steps
def post_to_inbox(activity: ap.BaseActivity) -> None:
    # actor = activity.get_actor()
    backend = ap.get_backend()

    # TODO: drop if emitter is blocked
    # backend.outbox_is_blocked(target actor, actor.id)

    # TODO: drop if duplicate
    # backend.inbox_check_duplicate(actor, activity.id)

    backend.save(Box.INBOX, activity)

    process_new_activity(activity)

    finish_inbox_processing(activity)


# TODO, this must move to Dramatiq queuing
def process_new_activity(activity: ap.BaseActivity) -> None:
    try:
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
            base_url = current_app.config["BASE_URL"]
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
        current_app.logger.exception(f"failed to process new activity" f" {activity.id}")
    except Exception as err:
        current_app.logger.exception(f"failed to process new activity" f" {activity.id}")


# TODO, this must move to Dramatiq queueing
def finish_inbox_processing(activity: ap.BaseActivity) -> None:
    try:
        backend = ap.get_backend()

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
    except Exception as err:
        current_app.logger.exception(f"failed to cache attachments for" f" {activity.id}")


def post_to_outbox(activity: ap.BaseActivity) -> str:
    if activity.has_type(ap.CREATE_TYPES):
        activity = activity.build_create()

    backend = ap.get_backend()

    # Assign a random ID
    obj_id = backend.random_object_id()
    activity.set_id(backend.activity_url(obj_id), obj_id)

    backend.save(Box.OUTBOX, activity)

    finish_post_to_outbox(activity.id)
    return activity.id


def finish_post_to_outbox(iri: str) -> None:
    try:
        activity = ap.fetch_remote_activity(iri)
        backend = ap.get_backend()

        current_app.logger.info(f"activity={activity!r}")

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
            post_to_remote_inbox(payload, recp)
    except (ActivityGoneError, ActivityNotFoundError):
        current_app.logger.exception(f"no retry")
    except Exception as err:
        current_app.logger.exception(f"failed to post " f"to remote inbox for {iri}")


def post_to_remote_inbox(payload: str, to: str) -> None:
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


def forward_activity(iri: str) -> None:
    try:
        activity = ap.fetch_remote_activity(iri)
        backend = ap.get_backend()
        recipients = backend.followers_as_recipients()
        current_app.logger.debug(f"Forwarding {activity!r} to {recipients}")
        activity = ap.clean_activity(activity.to_dict())
        for recp in recipients:
            current_app.logger.debug(f"forwarding {activity!r} to {recp}")
            payload = json.dumps(activity)
            post_to_remote_inbox(payload, recp)

    except Exception as err:
        current_app.logger.exception(f"failed to cache attachments for {iri}")


def send_update_profile(user: User) -> None:
    # FIXME: not sure at all about that
    actor = user.actor[0]
    raw_update = dict(
        to=[follower.actor.url for follower in actor.followers], actor=actor.to_dict(), object=actor.to_dict()
    )
    current_app.logger.debug(f"recipients: {raw_update['to']}")
    update = ap.Update(**raw_update)
    post_to_outbox(update)
