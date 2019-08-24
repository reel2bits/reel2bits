from flask import Blueprint, jsonify, request, abort
from app_oauth import require_oauth
from authlib.flask.oauth2 import current_token
from models import UserLogging

bp_api_account = Blueprint("bp_api_account", __name__)


@bp_api_account.route("/api/users/<string:username>/logs", methods=["GET"])
@require_oauth("read")
def logs(username):
    current_user = current_token.user
    if not current_user:
        return jsonify({"error": "Unauthorized"}), 403

    if current_user.name != username:
        return jsonify({"error": "Unauthorized"}), 403

    page = request.args.get("page", 1)
    if page == "null":
        abort(400)
    page = int(page)
    per_page = int(request.args.get("page_size", 20))

    logs = UserLogging.query.filter(UserLogging.user_id == current_user.id).paginate(page=page, per_page=per_page)

    items = []
    for log in logs.items:
        items.append(
            {
                "date": log.timestamp,
                "category": log.category,
                "level": log.level,
                "itemId": log.item_id,
                "message": log.message,
            }
        )

    resp = {"page": page, "page_size": per_page, "totalItems": logs.total, "items": items}
    return jsonify(resp)
