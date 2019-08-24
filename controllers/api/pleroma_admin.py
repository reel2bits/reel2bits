from flask import Blueprint, request, jsonify, abort
from models import db, User
from app_oauth import require_oauth
from authlib.flask.oauth2 import current_token

bp_api_pleroma_admin = Blueprint("bp_api_pleroma_admin", __name__)

# This API copy the pleroma one, so admin-fe can be used, at least with users, and basic usage


@bp_api_pleroma_admin.route("/api/pleroma/admin/users", methods=["GET"])
@require_oauth("read")
def list_users():
    user = current_token.user
    if not user.is_admin():
        abort(403)

    # query params, optionals
    # p_query = request.args.get("query", None)
    # p_filters = request.args.get("filters", None)
    p_page = int(request.args.get("page", 1))
    p_page_size = int(request.args.get("page_size", 50))
    # p_tags = request.args.get("tags", None)
    # p_name = request.args.get("name", None)
    # p_email = request.args.get("email", None)

    q = User.query.paginate(page=p_page, per_page=p_page_size)

    resp = {"page_size": p_page_size, "count": len(q.items), "users": []}
    for i in q.items:
        resp["users"].append(
            {
                "deactivated": False,
                "id": i.id,
                "nickname": i.name,
                "roles": {"admin": i.is_admin(), "moderator": False},  # not implemented, pleroma specific
                "local": True,
                "tags": [],  # not implemented, pleroma specific
            }
        )
    response = jsonify(resp)
    response.mimetype = "application/json; charset=utf-8"
    response.status_code = 200
    return response


@bp_api_pleroma_admin.route("/api/pleroma/admin/users", methods=["DELETE"])
@require_oauth("read")
def remove_user():
    user = current_token.user
    if not user.is_admin():
        abort(403)

    username = request.args.get("nickname", None)
    if not username:
        abort(400)

    # we need to delete user
    user = User.query.filter(User.name == username).one()
    if not user:
        abort(404)

    # FIXME: CASCADE stuff things
    db.session.delete(user.actor[0])
    db.session.delete(user)
    db.session.commit()

    response = jsonify(username)
    response.mimetype = "application/json; charset=utf-8"
    response.status_code = 200
    return response


@bp_api_pleroma_admin.route("/api/pleroma/admin/users/<int:user_id>", methods=["GET"])
@require_oauth("read")
def infos_user(user_id):
    user = current_token.user
    if not user.is_admin():
        abort(403)

    if not user_id:
        abort(400)

    user = User.query.filter(User.id == user_id).one()
    if not user:
        abort(404)

    return jsonify(
        id=user.id,
        username=user.name,
        acct=user.name,
        display_name=user.display_name,
        locked=False,
        created_at=user.created_at,
        followers_count=len(user.actor[0].followers),
        following_count=len(user.actor[0].followings),
        statuses_count=user.sounds.count(),
        note=user.actor[0].summary,
        url=user.actor[0].url,
        avatar="",
        avatar_static="",
        header="",
        header_static="",
        emojis=[],
        moved=None,
        fields=[],
        bot=False,
        source={
            "privacy": "unlisted",
            "sensitive": False,
            "language": user.locale,
            "note": user.actor[0].summary,
            "fields": [],
        },
        pleroma={"is_admin": user.is_admin()},
        tags=[],
        roles={"admin": user.is_admin(), "moderator": False},  # not implemented, pleroma specific
        local=True,
        deactivated=False,
        nickname=user.name,
    )


# placeholder, returns nothing for now
@bp_api_pleroma_admin.route("/api/pleroma/admin/users/<int:user_id>/statuses", methods=["GET"])
@require_oauth("read")
def statuses_user(user_id):
    # params: godmode
    user = current_token.user
    if not user.is_admin():
        abort(403)

    return jsonify([])


@bp_api_pleroma_admin.route("/api/pleroma/admin/*", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@require_oauth("read")
def unimplemented():
    user = current_token.user
    if not user.is_admin():
        abort(403)

    abort(501)  # not implemented
