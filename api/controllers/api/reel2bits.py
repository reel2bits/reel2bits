from flask import Blueprint, jsonify, request, abort, current_app, render_template
from models import db, User, PasswordResetToken, Sound
from utils.various import add_user_log, generate_random_token, add_log
from app_oauth import require_oauth
from authlib.flask.oauth2 import current_token
from flask_security.utils import hash_password, verify_password
from flask_mail import Message
import smtplib
from app import mail
from utils.defaults import Reel2bitsDefaults
from datas_helpers import default_genres

bp_api_reel2bits = Blueprint("bp_api_reel2bits", __name__)


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
    resp = []

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
