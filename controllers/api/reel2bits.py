from flask import Blueprint, jsonify, request
from models import db, licences
from utils import add_user_log
from app_oauth import require_oauth
from authlib.flask.oauth2 import current_token
from flask_security.utils import hash_password, verify_password

bp_api_reel2bits = Blueprint("bp_api_reel2bits", __name__)


@bp_api_reel2bits.route("/api/reel2bits/licenses", methods=["GET"])
def licenses():
    """
    List of various licenses.
    ---
    tags:
        - Tracks
    responses:
        200:
            description: Returns a list of various licenses.
    """
    resp = [licences[i] for i in licences]
    response = jsonify(resp)
    response.mimetype = "application/json; charset=utf-8"
    response.status_code = 200
    return response


@bp_api_reel2bits.route("/api/reel2bits/change_password", methods=["POST"])
@require_oauth("write")
def change_password():
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
