from flask import Blueprint, jsonify, request, abort, current_app, render_template
from models import db, User, PasswordResetToken, Sound, SoundTag, Actor, Follower
from utils.various import add_user_log, generate_random_token, add_log
from app_oauth import require_oauth
from authlib.flask.oauth2 import current_token
from flask_security.utils import hash_password, verify_password
from flask_mail import Message
import smtplib
import re
from utils.defaults import Reel2bitsDefaults
from datas_helpers import default_genres
from little_boxes.webfinger import get_actor_url
from little_boxes.urlutils import InvalidURLError
from little_boxes import activitypub as ap
from urllib.parse import urlparse
from sqlalchemy import or_, and_, not_

bp_api_reel2bits = Blueprint("bp_api_reel2bits", __name__)

RE_ACCOUNT = re.compile(r"^(?P<user>[\w]+)@(?P<instance>[\w.]+)$")


@bp_api_reel2bits.route("/api/reel2bits/licenses", methods=["GET"])
def licenses():
    """
    List of known licenses.
    ---
    tags:
        - Tracks
    responses:
        200:
            description: Returns a list of various licenses.
    """
    resp = [Reel2bitsDefaults.known_licences[i] for i in Reel2bitsDefaults.known_licences]
    response = jsonify(resp)
    response.mimetype = "application/json; charset=utf-8"
    response.status_code = 200
    return response


@bp_api_reel2bits.route("/api/reel2bits/genres", methods=["GET"])
def genres():
    """
    List of genres.
    ---
    tags:
        - Tracks
    parameters:
        - name: query
          in: query
          type: string
          required: false
          description: filter the returned list
    responses:
        200:
            description: Returns a list of genres from database and builtin.
    """
    genres_db = db.session.query(Sound.genre).group_by(Sound.genre)

    query = request.args.get("query", False)

    if query:
        genres_db = genres_db.filter(Sound.genre.ilike("%" + query + "%")).all()
        genres_db = [a.genre for a in genres_db]
        builtin_filtered = set(filter(lambda k: query.lower() in k.lower(), default_genres()))
        resp = list(set(genres_db).union(builtin_filtered))
    else:
        resp = list(set(genres_db.all()).union(set(default_genres())))

    response = jsonify(resp)
    response.mimetype = "application/json; charset=utf-8"
    response.status_code = 200
    return response


@bp_api_reel2bits.route("/api/reel2bits/tags", methods=["GET"])
def tags():
    """
    List of tags.
    ---
    tags:
        - Tracks
    parameters:
        - name: query
          in: query
          type: string
          required: false
          description: filter the returned list
    responses:
        200:
            description: Returns a list of tags from database.
    """
    tags_db = db.session.query(SoundTag.name).group_by(SoundTag.name)

    query = request.args.get("query", False)

    if query:
        tags_db = tags_db.filter(SoundTag.name.ilike("%" + query + "%")).all()

    resp = [a.name for a in tags_db]

    response = jsonify(resp)
    response.mimetype = "application/json; charset=utf-8"
    response.status_code = 200
    return response


@bp_api_reel2bits.route("/api/reel2bits/change_password", methods=["POST"])
@require_oauth("write")
def change_password():
    """
    Change user password.
    ---
    tags:
        - Accounts
    security:
        - OAuth2:
            - write
    responses:
        200:
            description: fixme.
    """
    user = current_token.user
    if not user:
        return jsonify({"error": "Unauthorized"}), 403

    password = request.form.get("password", None)
    new_password = request.form.get("new_password", None)
    new_password_confirmation = request.form.get("new_password_confirmation", None)

    if not password:
        return jsonify({"error": "password missing"}), 400
    if not new_password:
        return jsonify({"error": "new password missing"}), 400
    if not new_password_confirmation:
        return jsonify({"error": "new password confirmation missing"}), 400

    if new_password != new_password_confirmation:
        return jsonify({"error": "new password and confirmation doesn't match"}), 400

    if password == new_password:
        return jsonify({"error": "passwords are identical"}), 400

    new_hash = hash_password(new_password)
    # Check if old password match
    if verify_password(password, user.password):
        # change password
        user.password = new_hash
        db.session.commit()
        add_user_log(user.id, user.id, "user", "info", "Password changed")
        return jsonify({"status": "success"})
    return jsonify({"error": "old password doesn't match"}), 401


@bp_api_reel2bits.route("/api/reel2bits/reset_password", methods=["POST"])
def reset_password():
    """
    Ask for a reset password link by email.
    ---
    tags:
        - Accounts
    responses:
        200:
            description: fixme.
    """
    email = request.args.get("email", None)
    if not email:
        abort(400)

    user = User.query.filter(User.email == email).first()
    if not user:
        abort(404)

    # generate a reset link
    prt = PasswordResetToken()
    prt.token = generate_random_token()
    prt.expires_at = None
    prt.user_id = user.id

    db.session.add(prt)
    db.session.commit()
    add_user_log(user.id, user.id, "user", "info", "Password reset token generated")

    # Send email
    token_link = f"https://{current_app.config['AP_DOMAIN']}/password-reset/{prt.token}"
    msg = Message(subject="Password reset", recipients=[user.email], sender=current_app.config["MAIL_DEFAULT_SENDER"])
    msg.body = render_template("email/password_reset.txt", token_link=token_link, user=user)
    msg.html = render_template("email/password_reset.html", token_link=token_link, user=user)
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
            add_log("global", "ERROR", f"Error sending email for password reset user {user.id}: {err}")
            add_user_log(user.id, user.id, "user", "error", "An error occured while sending email")

    return jsonify({"status": "ok"}), 204


@bp_api_reel2bits.route("/api/reel2bits/reset_password/<string:token>", methods=["POST"])
def reset_password_token(token):
    """
    Change user password with token.
    ---
    tags:
        - Accounts
    responses:
        200:
            description: fixme.
    """
    new_password = request.json.get("new_password", None)
    new_password_confirmation = request.json.get("new_password_confirmation", None)

    if not new_password:
        return jsonify({"error": "new password missing"}), 400
    if not new_password_confirmation:
        return jsonify({"error": "new password confirmation missing"}), 400

    if new_password != new_password_confirmation:
        return jsonify({"error": "new password and confirmation doesn't match"}), 400

    new_hash = hash_password(new_password)
    # Check if the token is valid
    tok = PasswordResetToken.query.filter(PasswordResetToken.token == token).first()
    if not tok:
        return jsonify({"error": "invalid token"}), 404

    if tok.used:
        return jsonify({"error": "token already used"}), 400

    tok.user.password = new_hash
    tok.used = True
    db.session.commit()
    add_user_log(tok.user.id, tok.user.id, "user", "info", "Password have been changed")

    return jsonify({"status": "success"}), 204


@bp_api_reel2bits.route("/api/reel2bits/search", methods=["GET"])
@require_oauth(optional=True)
def search():
    """
    Search.
    ---
    tags:
        - Global
    parameters:
        - name: q
          in: query
          type: string
          required: true
          description: search string
    responses:
        200:
            description: fixme.
    """
    # Get logged in user from bearer token, or None if not logged in
    if current_token:
        current_user = current_token.user
    else:
        current_user = None

    s = request.args.get("q", None)
    if not s:
        return jsonify({"error": "No search string provided"}), 400

    # This is the old search endpoint and needs to be improved
    # Especially tracks and accounts needs to be returned in the right format, with the data helpers

    results = {"accounts": [], "sounds": [], "mode": None, "from": None}

    if current_user:
        results["from"] = current_user.name

    # Search for sounds
    # TODO: Implement FTS to get sounds search

    # Search for accounts
    accounts = []
    is_user_at_account = RE_ACCOUNT.match(s)

    if s.startswith("https://"):
        results["mode"] = "uri"
        if current_user:
            users = (
                db.session.query(Actor, Follower)
                .outerjoin(
                    Follower, and_(Actor.id == Follower.target_id, Follower.actor_id == current_user.actor[0].id)
                )
                .filter(Actor.url == s)
                .filter(not_(Actor.id == current_user.actor[0].id))
                .all()
            )
        else:
            users = db.session.query(Actor).filter(Actor.url == s).all()
    elif is_user_at_account:
        results["mode"] = "acct"
        user = is_user_at_account.group("user")
        instance = is_user_at_account.group("instance")
        if current_user:
            users = (
                db.session.query(Actor, Follower)
                .outerjoin(
                    Follower, and_(Actor.id == Follower.target_id, Follower.actor_id == current_user.actor[0].id)
                )
                .filter(Actor.preferred_username == user, Actor.domain == instance)
                .filter(not_(Actor.id == current_user.actor[0].id))
                .all()
            )
        else:
            users = db.session.query(Actor).filter(Actor.preferred_username == user, Actor.domain == instance).all()
    else:
        results["mode"] = "username"
        # Match actor username in database
        if current_user:
            users = (
                db.session.query(Actor, Follower)
                .outerjoin(
                    Follower, and_(Actor.id == Follower.target_id, Follower.actor_id == current_user.actor[0].id)
                )
                .filter(or_(Actor.preferred_username.contains(s), Actor.name.contains(s)))
                .filter(not_(Actor.id == current_user.actor[0].id))
                .all()
            )
        else:
            users = (
                db.session.query(Actor).filter(or_(Actor.preferred_username.contains(s), Actor.name.contains(s))).all()
            )

    # Handle the results
    if len(users) > 0:
        for user in users:
            if current_user:
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
                if follow_rel:
                    follow_status = follow_rel[1] is not None
                else:
                    follow_status = False

                domain = urlparse(iri["url"])
                user = {
                    "username": iri["name"],
                    "name": iri["preferredUsername"],
                    "instance": domain.netloc,
                    "url": iri["url"],
                    "remote": True,
                    "summary": iri["summary"],
                    "follow": follow_status,
                }
                accounts.append(user)
                results["mode"] = "webfinger"
                # Use iri to populate results["accounts"]
        except (InvalidURLError, ValueError):
            current_app.logger.exception(f"Invalid webfinger URL: {s}")

    # Finally fill the results dict
    results["accounts"] = accounts

    return jsonify({"who": s, "results": results})
