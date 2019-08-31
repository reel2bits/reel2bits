from flask import Blueprint, jsonify, request, url_for
from models import db, Sound, Activity
from app_oauth import require_oauth
import json
from models import licences as track_licenses
from datas_helpers import to_json_statuses, to_json_account


bp_api_v1_timelines = Blueprint("bp_api_v1_timelines", __name__)


@bp_api_v1_timelines.route("/api/v1/timelines/invalid", methods=["GET"])
@require_oauth(None)
def invalid():
    """
    Statuses from accounts the user follows.
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
    count = int(request.args.get("count"), 20)
    since_id = request.args.get("since_id", None)

    # Get logged in user from bearer token, or None if not logged in
    # current_user = current_token.user
    sounds = Sound.query.filter(Sound.private.is_(False), Sound.transcode_state == Sound.TRANSCODE_DONE).order_by(
        Sound.uploaded
    )
    if since_id:
        sounds = sounds.filter(Sound.flake_id >= since_id)

    resp = []

    for sound in sounds.limit(count):
        si = sound.sound_infos.first()

        url_orig = url_for("get_uploads_stuff", thing="sounds", stuff=sound.path_sound(orig=True))
        url_transcode = url_for("get_uploads_stuff", thing="sounds", stuff=sound.path_sound(orig=False))

        track_obj = {
            "id": sound.flake_id,
            "title": sound.title,
            "user": sound.user.name,
            "description": sound.description,
            "picture_url": None,  # FIXME not implemented yet
            "media_orig": url_orig,
            "media_transcoded": url_transcode,
            "waveform": (json.loads(si.waveform) if si else None),
            "private": sound.private,
            "uploaded_on": sound.uploaded,
            "uploaded_elapsed": sound.elapsed(),
            "album_id": (sound.album.flake_id if sound.album else None),
            "processing": {
                "basic": (si.done_basic if si else None),
                "transcode_state": sound.transcode_state,
                "transcode_needed": sound.transcode_needed,
                "done": sound.processing_done(),
            },
            "metadatas": {
                "licence": track_licenses[sound.licence],
                "duration": (si.duration if si else None),
                "type": (si.type if si else None),
                "codec": (si.codec if si else None),
                "format": (si.format if si else None),
                "channels": (si.channels if si else None),
                "rate": (si.rate if si else None),  # Hz
            },
        }
        if si:
            if si.bitrate and si.bitrate_mode:
                track_obj["metadatas"]["bitrate"] = si.bitrate
                track_obj["metadatas"]["bitrate_mode"] = si.bitrate_mode

        resp.append(track_obj)

    response = jsonify(resp)
    response.mimetype = "application/json; charset=utf-8"
    response.status_code = 200
    return response


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
    page = request.args.get("page", 1)

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
            tracks.append(to_json_statuses(t.Sound, to_json_account(t.Sound.user)))
        else:
            print(t.Activity)
    resp = {"page": page, "page_size": count, "totalItems": q.total, "items": tracks, "totalPages": q.pages}
    return jsonify(resp)
