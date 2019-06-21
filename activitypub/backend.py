from little_boxes import activitypub as ap
from flask import current_app
import requests
from models import db, Activity, create_remote_actor, Actor, update_remote_actor
from urllib.parse import urlparse
from .vars import Box
from version import VERSION


class Reel2BitsBackend(ap.Backend):
    def debug_mode(self) -> bool:
        return current_app.config["DEBUG"]

    def user_agent(self) -> str:
        url = current_app.config["BASE_URL"]
        return f"{requests.utils.default_user_agent()} " f"(reel2bits/{VERSION}; +{url})"

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

    def outbox_create(self, as_actor: ap.Person, create: ap.Create) -> None:
        self._handle_replies(as_actor, create)

    def outbox_update(self, as_actor: ap.Person, activity: ap.BaseActivity):
        current_app.logger.debug(f"outbox_update {activity!r} as {as_actor!r}")

    def outbox_delete(self, as_actor: ap.Person, activity: ap.BaseActivity) -> None:
        current_app.logger.debug(f"outbox_delete {activity!r} as {as_actor!r}")
        # Fetch linked activity and mark it deleted
        orig_activity = Activity.query.filter(Activity.url == activity.get_object().id, Activity.type == "Create").first()
        orig_activity.meta_deleted = True
        db.session.commit()

    def _handle_replies(self, as_actor: ap.Person, create: ap.Create) -> None:
        """Do magic about replies, we don't handle that for now"""
        in_reply_to = create.get_object().inReplyTo
        if not in_reply_to:
            return

        current_app.logger.error("!!! unhandled case: _handle_replies(in_reply_to=!None) !!!")
        return

    def _fetch_iri(self, iri: str) -> ap.ObjectType:
        base_url = current_app.config["BASE_URL"]

        if not iri:
            return None

        # Check if owned
        if iri.startswith(base_url):
            actor = Actor.query.filter(Actor.url == iri).first()
            if actor:
                current_app.logger.debug(f"fetch_iri: owned local actor {actor!r}")
                return actor.to_dict()

            activity = Activity.query.filter(Activity.url == iri, Activity.box == Box.OUTBOX.value).first()
            if activity:
                current_app.logger.debug(f"fetch_iri: owned local activity {activity!r}")
                return activity.payload
        else:
            # Check if in the inbox
            activity = Activity.query.filter(Activity.url == iri).first()
            if activity:
                current_app.logger.debug(f"fetch_iri: local activity {activity!r}")
                return activity.payload

        current_app.logger.debug(f"fetch_iri: cannot find locally, fetching remote")
        return super().fetch_iri(iri)

    def fetch_iri(self, iri: str) -> ap.ObjectType:
        current_app.logger.debug(f"asked to fetch {iri}")
        return self._fetch_iri(iri)

    def inbox_update(self, as_actor: ap.Person, update: ap.Update) -> None:
        obj = update.get_object()
        current_app.logger.debug(f"inbox_update {obj.ACTIVITY_TYPE} {obj!r} as {as_actor!r}")

        db_actor = Actor.query.filter(Actor.url == as_actor.id).first()
        if not db_actor:
            current_app.logger.error(f"cannot find actor {as_actor!r}")
            return

        if obj.ACTIVITY_TYPE == ap.ActivityType.PERSON:
            update_remote_actor(db_actor.id, obj)
        else:
            raise NotImplementedError
