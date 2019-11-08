from flask import Blueprint, jsonify, request, abort, current_app, render_template
from models import db, User, PasswordResetToken, Sound, SoundTag, Actor, Follower, create_remote_actor, Config, Activity
from utils.various import add_user_log, generate_random_token, add_log
from datas_helpers import to_json_account, to_json_relationship, default_genres, to_json_track
from app_oauth import require_oauth
from authlib.flask.oauth2 import current_token
from flask_security.utils import hash_password, verify_password
from flask_mail import Message
import smtplib
import re
from utils.defaults import Reel2bitsDefaults
from little_boxes.webfinger import get_actor_url
from little_boxes.urlutils import InvalidURLError
from little_boxes import activitypub as ap
from activitypub.vars import Box
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

    _config = Config.query.first()
    if not _config:
        print("ERROR: cannot get instance Config from database")
    instance = {"name": None, "url": None}
    if _config:
        instance["name"] = _config.app_name
    instance["url"] = current_app.config["REEL2BITS_URL"]
    msg.body = render_template("email/password_reset.txt", token_link=token_link, user=user, instance=instance)
    msg.html = render_template("email/password_reset.html", token_link=token_link, user=user, instance=instance)
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
    # Users should be searched from known Actors or fetched
    # URI should be searched from known activities or fetched
    # FTS, well, FTS needs to be implemented

    results = {"accounts": [], "sounds": [], "mode": None, "from": None}

    if current_user:
        results["from"] = current_user.name

    # Search for sounds
    # TODO: Implement FTS to get sounds search
    sounds = []

    # Search for accounts
    accounts = []
    is_user_at_account = RE_ACCOUNT.match(s)

    if s.startswith("https://"):
        # Try to match the URI from Activities in database
        results["mode"] = "uri"
        users = Actor.query.filter(Actor.meta_deleted.is_(False), Actor.url == s).all()
    elif is_user_at_account:
        # It matches user@some.where.tld, try to match it locally
        results["mode"] = "acct"
        user = is_user_at_account.group("user")
        instance = is_user_at_account.group("instance")
        users = Actor.query.filter(
            Actor.meta_deleted.is_(False), Actor.preferred_username == user, Actor.domain == instance
        ).all()
    else:
        # It's a FTS search
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

    # Handle the found users
    if len(users) > 0:
        for actor in users:
            relationship = False
            if current_user:
                relationship = to_json_relationship(current_user, actor.user)
            accounts.append(to_json_account(actor.user, relationship))

    if len(accounts) <= 0:
        # Do a webfinger
        # TODO FIXME: We should do this only if https:// or user@account submitted
        # And rework it slightly differently since we needs to backend.fetch_iri() for https:// who
        # can match a Sound and not only an Actor
        current_app.logger.debug(f"webfinger for {s}")
        try:
            remote_actor_url = get_actor_url(s, debug=current_app.debug)
            # We need to get the remote Actor
            backend = ap.get_backend()
            iri = backend.fetch_iri(remote_actor_url)
            if iri:
                # We have fetched an unknown Actor
                # Save it in database and return it properly
                current_app.logger.debug(f"got remote actor URL {remote_actor_url}")

                act = ap.parse_activity(iri)

                fetched_actor, fetched_user = create_remote_actor(act)
                db.session.add(fetched_user)
                db.session.add(fetched_actor)
                db.session.commit()

                relationship = False
                if current_user:
                    relationship = to_json_relationship(current_user, fetched_user)
                accounts.append(to_json_account(fetched_user, relationship))
                results["mode"] = "webfinger"

        except (InvalidURLError, ValueError):
            current_app.logger.exception(f"Invalid AP URL: {s}")
            # Then test fetching as a "normal" Activity ?
    # Finally fill the results dict
    results["accounts"] = accounts

    # FIXME: handle exceptions
    if results["mode"] == "uri" and len(sounds) <= 0:
        backend = ap.get_backend()
        iri = backend.fetch_iri(s)
        if iri:
            # FIXME: Is INBOX the right choice here ?
            backend.save(Box.INBOX, iri)
        # Fetch again, but get it from database
        activity = Activity.query.filter(Activity.url == iri).first()
        if not activity:
            current_app.logger.exception("WTF Activity is not saved")
        else:
            from tasks import create_sound_for_remote_track, fetch_remote_track

            sound_id = create_sound_for_remote_track(activity)
            sound = Sound.query.filter(Sound.id == sound_id).one()
            fetch_remote_track.delay(sound.id)
            relationship = False
            if current_user:
                relationship = to_json_relationship(current_user, sound.user)
            acct = to_json_account(sound.user, relationship)
            sounds.append(to_json_track(sound, acct))

    return jsonify({"who": s, "results": results})
