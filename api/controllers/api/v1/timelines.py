from flask import Blueprint, jsonify, request, abort
from models import db, Sound, Activity, Album, User
from app_oauth import require_oauth
from datas_helpers import to_json_track, to_json_account, to_json_album, to_json_relationship
from authlib.flask.oauth2 import current_token


bp_api_v1_timelines = Blueprint("bp_api_v1_timelines", __name__)


@bp_api_v1_timelines.route("/api/v1/timelines/home", methods=["GET"])
@require_oauth("read")
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
    # TODO don't forget to handle if paginated=true paginate else mastoapi
    resp = {"page": 1, "page_size": 20, "totalItems": 0, "items": [], "totalPages": 1}
    return jsonify(resp)


@bp_api_v1_timelines.route("/api/v1/timelines/public", methods=["GET"])
@require_oauth(optional=True)
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

    paginated = request.args.get("paginated", False)
    count = int(request.args.get("count", 20))
    local_only = request.args.get("local", False)

    q = db.session.query(Activity, Sound).filter(
        Activity.type == "Create", Activity.payload[("object", "type")].astext == "Audio"
    )
    q = q.filter(Activity.meta_deleted.is_(False))

    if local_only:
        q = q.filter(Activity.local.is_(True))

    q = q.filter(Activity.payload["to"].astext.contains("https://www.w3.org/ns/activitystreams#Public"))

    q = q.join(Sound, Sound.activity_id == Activity.id)
    q = q.order_by(Activity.creation_date.desc())

    if paginated:
        # Render timeline as paginated
        page = int(request.args.get("page", 1))

        q = q.paginate(page=page, per_page=count)

        tracks = []
        for t in q.items:
            if t.Sound:
                relationship = False
                if current_token and current_token.user:
                    relationship = to_json_relationship(current_token.user, t.Sound.user)
                account = to_json_account(t.Sound.user, relationship)
                tracks.append(to_json_track(t.Sound, account))
            else:
                print(t.Activity)
        resp = {"page": page, "page_size": count, "totalItems": q.total, "items": tracks, "totalPages": q.pages}
        return jsonify(resp)
    else:
        # mastoapi compatible
        since_id = request.args.get("since_id")

        # since then we want the timeline
        if since_id:
            q = q.filter(Sound.flake_id > since_id)

        # then limit count
        q = q.limit(count)

        tracks = []
        for t in q.all():
            if t.Sound:
                relationship = False
                if current_token and current_token.user:
                    relationship = to_json_relationship(current_token.user, t.Sound.user)
                account = to_json_account(t.Sound.user, relationship)
                tracks.append(to_json_track(t.Sound, account))
            else:
                print(t.Activity)
        return jsonify(tracks)


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

    q = Sound.query.filter(
        Sound.user_id == user.id, Sound.private.is_(True), Sound.transcode_state == Sound.TRANSCODE_DONE
    )

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
@require_oauth(optional=True)
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
          description: the user flake id to get albums list
    responses:
        200:
            description: Returns array of Status
    """
    count = int(request.args.get("count", 20))
    page = int(request.args.get("page", 1))
    user = request.args.get("user", None)
    if not user:
        abort(400)

    user = User.query.filter(User.flake_id == user).first()
    if not user:
        return jsonify({"error": "User does not exist"}), 404

    q = Album.query.order_by(Album.created.desc())

    only_public = True
    if current_token and current_token.user:
        if user.id == current_token.user.id:
            only_public = False

    if only_public:
        q = q.filter(Album.user_id == user.id, Album.private.is_(False))
    else:
        q = q.filter(Album.user_id == current_token.user.id)

    q = q.paginate(page=page, per_page=count)

    albums = []
    for t in q.items:
        relationship = False
        if current_token and current_token.user:
            relationship = to_json_relationship(current_token.user, t.user)
        account = to_json_account(t.user, relationship)
        albums.append(to_json_album(t, account))
    resp = {"page": page, "page_size": count, "totalItems": q.total, "items": albums, "totalPages": q.pages}
    return jsonify(resp)


@bp_api_v1_timelines.route("/api/v1/timelines/unprocessed", methods=["GET"])
@require_oauth("read")
def unprocessed():
    """
    User unprocessed tracks timeline.
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

    q = Sound.query.filter(
        Sound.user_id == user.id,
        Sound.transcode_state.in_((Sound.TRANSCODE_WAITING, Sound.TRANSCODE_PROCESSING, Sound.TRANSCODE_ERROR)),
    )

    q = q.order_by(Sound.uploaded.desc())

    q = q.paginate(page=page, per_page=count)

    tracks = []
    for t in q.items:
        relationship = to_json_relationship(current_token.user, t.user)
        account = to_json_account(t.user, relationship)
        tracks.append(to_json_track(t, account))
    resp = {"page": page, "page_size": count, "totalItems": q.total, "items": tracks, "totalPages": q.pages}
    return jsonify(resp)
