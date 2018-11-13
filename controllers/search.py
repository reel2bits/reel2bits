from flask import Blueprint, render_template, request, current_app
from flask_babelex import gettext

from models import db, Follower, Actor
from little_boxes.webfinger import get_actor_url
from little_boxes.urlutils import InvalidURLError
from little_boxes import activitypub as ap
from urllib.parse import urlparse
from flask_security import current_user
from sqlalchemy import or_

import re

bp_search = Blueprint("bp_search", __name__)

RE_ACCOUNT = re.compile(r"^(?P<user>[\w]+)@(?P<instance>[\w.]+)$")


@bp_search.route("/search", methods=["GET"])
def search():
    s = request.args.get("what")
    pcfg = {"title": gettext("Search user")}

    results = {"accounts": [], "sounds": [], "mode": None, "from": None}

    if current_user.is_authenticated:
        results["from"] = current_user.name

    # Search for sounds
    # TODO: Implement FTS to get sounds search

    # Search for accounts
    accounts = []
    is_user_at_account = RE_ACCOUNT.match(s)

    if s.startswith("https://"):
        results["mode"] = "uri"
        if current_user.is_authenticated:
            users = (
                db.session.query(Actor, Follower)
                .outerjoin(Follower, Actor.id == Follower.target_id)
                .filter(Actor.url == s)
                .filter(Follower.actor_id == current_user.actor[0].id)  # Remove the duplicates follows
                .all()
            )
        else:
            users = db.session.query(Actor).filter(Actor.url == s).all()
    elif is_user_at_account:
        results["mode"] = "acct"
        user = is_user_at_account.group("user")
        instance = is_user_at_account.group("instance")
        if current_user.is_authenticated:
            users = (
                db.session.query(Actor, Follower)
                .outerjoin(Follower, Actor.id == Follower.target_id)
                .filter(Actor.preferred_username == user, Actor.domain == instance)
                .filter(Follower.actor_id == current_user.actor[0].id)  # Remove the duplicates follows
                .all()
            )
        else:
            users = db.session.query(Actor).filter(Actor.preferred_username == user, Actor.domain == instance).all()
    else:
        results["mode"] = "username"
        # Match actor username in database
        if current_user.is_authenticated:
            users = (
                db.session.query(Actor, Follower)
                .join(Follower, Actor.id == Follower.target_id)
                .filter(or_(Actor.preferred_username.contains(s), Actor.name.contains(s)))
                .filter(Follower.actor_id == current_user.actor[0].id)  # Remove the duplicates follows
                .all()
            )
        else:
            users = (
                db.session.query(Actor).filter(or_(Actor.preferred_username.contains(s), Actor.name.contains(s))).all()
            )

    # Handle the results
    if len(users) > 0:
        for user in users:
            if current_user.is_authenticated:
                if user[1]:
                    follows = user[1].actor_id == current_user.actor[0].id
                else:
                    follows = False
            else:
                follows = None

            if type(user) is Actor:
                # Unauthenticated results
                accounts.append(
                    {
                        "username": user.name,
                        "name": user.preferred_username,
                        "summary": user.summary,
                        "instance": user.domain,
                        "url": user.url,
                        "remote": not user.is_local(),
                        "follow": follows,
                    }
                )
            else:
                accounts.append(
                    {
                        "username": user[0].name,
                        "name": user[0].preferred_username,
                        "summary": user[0].summary,
                        "instance": user[0].domain,
                        "url": user[0].url,
                        "remote": not user[0].is_local(),
                        "follow": follows,
                    }
                )

    if len(accounts) <= 0:
        # Do a webfinger
        current_app.logger.debug(f"webfinger for {s}")
        try:
            remote_actor_url = get_actor_url(s, debug=current_app.debug)
            # We need to get the remote Actor
            backend = ap.get_backend()
            iri = backend.fetch_iri(remote_actor_url)
            if iri:
                current_app.logger.debug(f"got remote actor URL {remote_actor_url}")
                # Fixme handle unauthenticated users plus duplicates follows
                follow_rel = (
                    db.session.query(Actor.id, Follower.id)
                    .outerjoin(Follower, Actor.id == Follower.target_id)
                    .filter(Actor.url == remote_actor_url)
                    .first()
                )
                follow_status = follow_rel[1] is not None

                domain = urlparse(iri["url"])
                user = {
                    "username": iri["name"],
                    "name": iri["preferredUsername"],
                    "instance": domain.netloc,
                    "url": iri["url"],
                    "remote": True,
                    "follow": follow_status,
                }
                accounts.append(user)
                results["mode"] = "webfinger"
                # Use iri to populate results["accounts"]
        except (InvalidURLError, ValueError):
            current_app.logger.exception(f"Invalid webfinger URL: {s}")

    # Finally fill the results dict
    results["accounts"] = accounts

    return render_template("search/results.jinja2", pcfg=pcfg, who=s, results=results)
