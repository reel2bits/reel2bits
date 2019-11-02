import pytz
import requests
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, jsonify, current_app
from flask_babelex import gettext
from flask_security import login_required, current_user

from forms import UserProfileForm
from models import db, User, Sound, Album, Follower, Actor, Activity, create_remote_actor
from utils import add_user_log
from flask_accept import accept_fallback
from little_boxes.webfinger import get_actor_url
from little_boxes.urlutils import InvalidURLError
from little_boxes import activitypub as ap
from tasks import post_to_outbox, send_update_profile

bp_users = Blueprint("bp_users", __name__)


@bp_users.route("/user/<string:name>", methods=["GET"])
@accept_fallback
def profile(name):
    pcfg = {"title": gettext("%(username)s' profile", username=name)}

    user = User.query.filter(User.name == name).first()
    if not user:
        flash(gettext("User not found"), "error")
        return redirect(url_for("bp_main.home"))

    if current_user.is_authenticated and user.id == current_user.id:
        sounds = Sound.query.filter(Sound.user_id == user.id)
    else:
        sounds = Sound.query.filter(
            Sound.user_id == user.id, Sound.private.is_(False), Sound.transcode_state == Sound.TRANSCODE_DONE
        )

    # FIXME better SQL for counting thoses relations
    followings = len(user.actor[0].followings)
    followers = len(user.actor[0].followers)

    return render_template(
        "users/profile.jinja2", pcfg=pcfg, user=user, sounds=sounds, followings=followings, followers=followers
    )


@bp_users.route("/user/<string:name>", methods=["GET"])
@profile.support("application/json", "application/activity+json")
def actor_json(name):
    user = User.query.filter(User.name == name).first()
    if not user:
        return Response("", status=404)
    actors = user.actor
    if len(actors) <= 0:
        return Response("", status=500)

    response = jsonify(actors[0].to_dict())
    response.mimetype = "application/activity+json; charset=utf-8"
    return response


@bp_users.route("/user/<string:name>/sets", methods=["GET"])
def profile_albums(name):
    pcfg = {"title": gettext("%(username)s' profile", username=name)}

    user = User.query.filter(User.name == name).first()
    if not user:
        flash(gettext("User not found"), "error")
        return redirect(url_for("bp_main.home"))

    if current_user.is_authenticated and user.id == current_user.id:
        albums = Album.query.filter(Album.user_id == user.id)
    else:
        albums = Album.query.filter(Album.user_id == user.id, Album.private.is_(False))

    return render_template("users/profile_albums.jinja2", pcfg=pcfg, user=user, albums=albums)


@bp_users.route("/account/edit", methods=["GET", "POST"])
@login_required
def edit():
    pcfg = {"title": gettext("Edit my profile")}

    user = User.query.filter(User.id == current_user.id).first()
    if not user:
        flash(gettext("User not found"), "error")
        return redirect(url_for("bp_main.home"))

    form = UserProfileForm(request.form, obj=user)
    form.timezone.choices = [[str(i), str(i)] for i in pytz.all_timezones]

    if form.validate_on_submit():
        user.timezone = form.timezone.data
        user.locale = form.locale.data
        user.display_name = form.display_name.data

        db.session.commit()

        # log
        add_user_log(user.id, user.id, "user", "info", "Edited user profile")

        flash(gettext("Profile updated"), "success")

        # trigger a profile update
        send_update_profile(user)

        return redirect(url_for("bp_users.profile", name=user.name))

    return render_template("users/edit.jinja2", pcfg=pcfg, form=form, user=user)


@bp_users.route("/account/follow", methods=["GET"])
@login_required
def follow():
    user = request.args.get("user")

    actor_me = current_user.actor[0]

    if user.startswith("https://"):
        actor = Actor.query.filter(Actor.url == user).first()
        if actor:
            local_user = actor.user
        else:
            local_user = None
    else:
        local_user = User.query.filter(User.name == user).first()

    if local_user:
        # Process local follow
        actor_me.follow(None, local_user.actor[0])
        flash(gettext("Follow successful"), "success")
    else:
        # Might be a remote follow

        # 1. Webfinger the user
        try:
            remote_actor_url = get_actor_url(user, debug=current_app.debug)
        except InvalidURLError:
            current_app.logger.exception(f"Invalid webfinger URL: {user}")
            remote_actor_url = None
        # except requests.exceptions.HTTPError:
        #    current_app.logger.exception(f"Invali webfinger URL: {user}")
        #    remote_actor_url = None

        if not remote_actor_url:
            flash(gettext("User not found"), "error")
            return redirect(url_for("bp_users.profile", name=current_user.name))

        # 2. Check if we have a local user
        actor_target = Actor.query.filter(Actor.url == remote_actor_url).first()

        if not actor_target:
            # 2.5 Fetch and save remote actor
            backend = ap.get_backend()
            iri = backend.fetch_iri(remote_actor_url)
            if not iri:
                flash(gettext("User not found"), "error")
                return redirect(url_for("bp_main.home"))
            act = ap.parse_activity(iri)
            actor_target, user_target = create_remote_actor(act)
            db.session.add(user_target)
            db.session.add(actor_target)

        # 2.7 Check if we already have a relation
        rel = Follower.query.filter(Follower.actor_id == actor_me.id, Follower.target_id == actor_target.id).first()

        if not rel:
            # 3. Initiate a Follow request from actor_me to actor_target
            follow = ap.Follow(actor=actor_me.url, object=actor_target.url)
            post_to_outbox(follow)
            flash(gettext("Follow request have been transmitted"), "success")
        else:
            flash(gettext("You already follow this user", "info"))

    return redirect(url_for("bp_users.profile", name=current_user.name))


@bp_users.route("/account/unfollow", methods=["GET"])
@login_required
def unfollow():
    user = request.args.get("user")

    actor_me = current_user.actor[0]

    if user.startswith("https://"):
        actor = Actor.query.filter(Actor.url == user).first()
        local_user = actor.user
    else:
        local_user = User.query.filter(User.name == user).first()

    if local_user:
        # Process local unfollow
        actor_me.unfollow(local_user.actor[0])
        flash(gettext("Unfollow successful"), "success")
    else:
        # Might be a remote unfollow

        # 1. Webfinger the user
        try:
            remote_actor_url = get_actor_url(user, debug=current_app.debug)
        except InvalidURLError:
            current_app.logger.exception(f"Invalid webfinger URL: {user}")
            remote_actor_url = None
        except requests.exceptions.HTTPError:
            current_app.logger.exception(f"Invali webfinger URL: {user}")
            remote_actor_url = None

        if not remote_actor_url:
            flash(gettext("User not found"), "error")
            return redirect(url_for("bp_users.profile", name=current_user.name))

        # 2. Check if we have a local user
        actor_target = Actor.query.filter(Actor.url == remote_actor_url).first()

        if not actor_target:
            # 2.5 Fetch and save remote actor
            backend = ap.get_backend()
            iri = backend.fetch_iri(remote_actor_url)
            if not iri:
                flash(gettext("User not found"), "error")
                return redirect(url_for("bp_main.home"))
            act = ap.parse_activity(iri)
            actor_target, user_target = create_remote_actor(act)
            db.session.add(user_target)
            db.session.add(actor_target)

        # 2.5 Get the relation of the follow
        follow_relation = Follower.query.filter(
            Follower.actor_id == actor_me.id, Follower.target_id == actor_target.id
        ).first()
        if not follow_relation:
            flash(gettext("You don't follow this user"), "error")
            return redirect(url_for("bp_users.profile", name=current_user.name))

        # 3. Fetch the Activity of the Follow
        accept_activity = Activity.query.filter(Activity.url == follow_relation.activity_url).first()
        if not accept_activity:
            current_app.logger.error(f"cannot find accept activity {follow_relation.activity_url}")
            flash(gettext("Whoops, something went wrong"))
            return redirect(url_for("bp_users.profile", name=current_user.name))
        # Then the Activity ID of the Accept will be the object id
        activity = ap.parse_activity(payload=accept_activity.payload)

        # Get the final activity (the Follow one)
        follow_activity = Activity.query.filter(Activity.url == activity.get_object_id()).first()
        if not follow_activity:
            current_app.logger.error(f"cannot find follow activity {activity.get_object_id()}")
            flash(gettext("Whoops, something went wrong"))
            return redirect(url_for("bp_users.profile", name=current_user.name))

        ap_follow_activity = ap.parse_activity(payload=follow_activity.payload)

        # 4. Initiate a Follow request from actor_me to actor_target
        unfollow = ap_follow_activity.build_undo()
        post_to_outbox(unfollow)
        flash(gettext("Unfollow request have been transmitted"), "success")

    return redirect(url_for("bp_users.profile", name=current_user.name))
