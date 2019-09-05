from flask import Blueprint, jsonify, request, abort
from models import db, Sound, Activity, Album, User
from app_oauth import require_oauth
from datas_helpers import to_json_track, to_json_account, to_json_album, to_json_relationship
from authlib.flask.oauth2 import current_token


bp_api_v1_timelines = Blueprint("bp_api_v1_timelines", __name__)


@bp_api_v1_timelines.route("/api/v1/timelines/home", methods=["GET"])
@require_oauth(None)
def home():
    """
    User friends statuses.
    ---
    tags:
        - Timelines
    parameters:
        - name: count
          in: query
          type: integer
          required: true
          description: count
        - name: with_muted
          in: query
          type: boolean
          required: true
          description: with muted users
        - name: since_id
          in: query
          type: string
          description: last ID
    responses:
        200:
            description: Returns array of Status
    """
    return jsonify([])


@bp_api_v1_timelines.route("/api/v1/timelines/public", methods=["GET"])
@require_oauth(None)
def public():
    """
    Public or TWKN statuses.
    ---
    tags:
        - Timelines
    parameters:
        - name: count
          in: query
          type: integer
          required: true
          description: count
        - name: with_muted
          in: query
          type: boolean
          required: true
          description: with muted users
        - name: local
          in: query
          type: boolean
          description: local only or TWKN
    responses:
        200:
            description: Returns array of Status
    """
    # Caveats: only handle public Sounds since we either federate (public) or no
    local_only = request.args.get("local", False)
    count = int(request.args.get("count", 20))
    page = int(request.args.get("page", 1))

    q = db.session.query(Activity, Sound).filter(
        Activity.type == "Create", Activity.payload[("object", "type")].astext == "Audio"
    )
    q = q.filter(Activity.meta_deleted.is_(False))

    if local_only:
        q = q.filter(Activity.local.is_(True))

    q = q.filter(Activity.payload["to"].astext.contains("https://www.w3.org/ns/activitystreams#Public"))

    q = q.join(Sound, Sound.activity_id == Activity.id)
    q = q.order_by(Activity.creation_date.desc())

    q = q.paginate(page=page, per_page=count)

    tracks = []
    for t in q.items:
        if t.Sound:
            relationship = False
            if current_token.user:
                relationship = to_json_relationship(current_token.user, t.Sound.user)
            account = to_json_account(t.Sound.user, relationship)
            tracks.append(to_json_track(t.Sound, account))
        else:
            print(t.Activity)
    resp = {"page": page, "page_size": count, "totalItems": q.total, "items": tracks, "totalPages": q.pages}
    return jsonify(resp)


@bp_api_v1_timelines.route("/api/v1/timelines/drafts", methods=["GET"])
@require_oauth("read")
def drafts():
    """
    User drafts timeline.
    ---
    tags:
        - Timelines
    parameters:
        - name: count
          in: query
          type: integer
          required: true
          description: count
        - name: page
          in: query
          type: integer
          description: page number
    responses:
        200:
            description: Returns array of Status
    """
    user = current_token.user
    if not user:
        return jsonify({"error": "Unauthorized"}), 403

    count = int(request.args.get("count", 20))
    page = int(request.args.get("page", 1))

    q = Sound.query.filter(Sound.user_id == user.id, Sound.private.is_(True))

    q = q.order_by(Sound.uploaded.desc())

    q = q.paginate(page=page, per_page=count)

    tracks = []
    for t in q.items:
        relationship = to_json_relationship(current_token.user, t.user)
        account = to_json_account(t.user, relationship)
        tracks.append(to_json_track(t, account))
    resp = {"page": page, "page_size": count, "totalItems": q.total, "items": tracks, "totalPages": q.pages}
    return jsonify(resp)


@bp_api_v1_timelines.route("/api/v1/timelines/albums", methods=["GET"])
@require_oauth(None)
def albums():
    """
    User albums timeline.
    ---
    tags:
        - Timelines
    parameters:
        - name: count
          in: query
          type: integer
          required: true
          description: count
        - name: page
          in: query
          type: integer
          description: page number
        - name: user
          in: query
          type: string
          description: the user ID to get albums list
    responses:
        200:
            description: Returns array of Status
    """
    tok_user = current_token.user
    count = int(request.args.get("count", 20))
    page = int(request.args.get("page", 1))
    user = request.args.get("user", None)
    if not user:
        abort(400)

    user = User.query.filter(User.id == user).first()
    if not user:
        return jsonify({"error": "User does not exist"}), 404

    q = Album.query.order_by(Album.created.desc())

    only_public = True
    if tok_user:
        if user.id == tok_user.id:
            only_public = False

    if only_public:
        q = q.filter(Album.user_id == user.id, Album.private.is_(False))
    else:
        q = q.filter(Album.user_id == tok_user.id)

    q = q.paginate(page=page, per_page=count)

    albums = []
    for t in q.items:
        relationship = False
        if current_token.user:
            relationship = to_json_relationship(current_token.user, t.user)
        account = to_json_account(t.user, relationship)
        albums.append(to_json_album(t, account))
    resp = {"page": page, "page_size": count, "totalItems": q.total, "items": albums, "totalPages": q.pages}
    return jsonify(resp)
