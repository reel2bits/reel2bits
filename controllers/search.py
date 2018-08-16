from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_babelex import gettext

from models import db, User, Follower, Actor
from little_boxes.webfinger import get_actor_url
from little_boxes.urlutils import InvalidURLError
from little_boxes import activitypub as ap
from urllib.parse import urlparse
from flask_security import current_user

bp_search = Blueprint("bp_search", __name__, url_prefix="/search")


@bp_search.route("/users", methods=["GET"])
def users():
    who = request.args.get("who")
    pcfg = {"title": gettext("Search user")}

    # No follow status for unauthenticated user search
    if not current_user.is_authenticated:
        local_users = User.query.filter(User.name.contains(who)).all()

        if len(local_users) > 0:
            return render_template("search/local_users_unauth.jinja2", pcfg=pcfg, who=who, users=local_users)
    else:
        # (user, actor, follower) tuple
        local_users = (
            db.session.query(User, Actor, Follower)
            .join(Actor, User.id == Actor.user_id)
            .outerjoin(Follower, Actor.id == Follower.target_id)
            .filter(User.name.contains(who))
            .all()
        )

        if len(local_users) > 0:
            return render_template("search/local_users_auth.jinja2", pcfg=pcfg, who=who, users=local_users)

        if not local_users:
            current_app.logger.debug(f"searching for {who}")
            try:
                remote_actor_url = get_actor_url(who, debug=current_app.debug)
            except (InvalidURLError, ValueError):
                current_app.logger.exception(f"Invalid webfinger URL: {who}")
                remote_actor_url = None

            if not remote_actor_url:
                flash(gettext("User not found"), "error")
                return redirect(url_for("bp_main.home"))

            # We need to get the remote Actor
            backend = ap.get_backend()
            iri = backend.fetch_iri(remote_actor_url)
            if not iri:
                flash(gettext("User not found"), "error")
                return redirect(url_for("bp_main.home"))

            current_app.logger.debug(f"got remote actor URL {remote_actor_url}")

            follow_rel = (
                db.session.query(Actor.id, Follower.id)
                .outerjoin(Follower, Actor.id == Follower.target_id)
                .filter(Actor.url == remote_actor_url)
                .first()
            )
            follow_status = follow_rel[1] is not None

            domain = urlparse(iri["url"])
            user = {
                "name": iri["preferredUsername"],
                "instance": domain.netloc,
                "url": iri["url"],
                "follow": follow_status,
            }

            return render_template("search/remote_user.jinja2", pcfg=pcfg, who=who, user=user)
