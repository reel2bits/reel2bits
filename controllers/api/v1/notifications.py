from flask import Blueprint, jsonify
from app_oauth import require_oauth


bp_api_v1_notifications = Blueprint("bp_api_v1_notifications", __name__)


@bp_api_v1_notifications.route("/api/v1/notifications", methods=["GET"])
@require_oauth("read")
def notifications():
    """
    Notifications concerning the user.
    ---
    tags:
        - Notifications
    responses:
        200:
            description: Returns a list of Notifications.
    """

    response = jsonify([])
    response.mimetype = "application/json; charset=utf-8"
    response.status_code = 200
    return response
