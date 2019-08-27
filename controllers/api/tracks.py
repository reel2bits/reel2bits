from flask import Blueprint, request, jsonify, url_for
from app_oauth import require_oauth
from authlib.flask.oauth2 import current_token
from forms import SoundUploadForm
from models import db, Sound, User
from models import licences as track_licenses
import json
from utils import add_user_log, get_hashed_filename
from flask_uploads import UploadSet, AUDIO

bp_api_tracks = Blueprint("bp_api_tracks", __name__)

sounds = UploadSet("sounds", AUDIO)


@bp_api_tracks.route("/api/tracks", methods=["POST"])
@require_oauth("write")
def upload():
    """
    Create a new track.
    ---
    tags:
        - Tracks
    security:
        - OAuth2:
            - write
    responses:
        200:
            description: Returns the track id and slug.
    """
    errors = {}

    current_user = current_token.user
    if not current_user:
        return jsonify({"error": "Unauthorized"}), 403

    if "file" not in request.files:
        errors["file"] = "No file present"

    if len(errors) > 0:
        return jsonify({"error": errors}), 400

    form = SoundUploadForm()

    if form.validate_on_submit():
        filename_orig = request.files["file"].filename
        filename_hashed = get_hashed_filename(filename_orig)

        sounds.save(request.files["file"], folder=current_user.slug, name=filename_hashed)

        rec = Sound()
        rec.filename = filename_hashed
        rec.filename_orig = filename_orig
        rec.licence = form.licence.data
        if form.album.data:
            rec.album_id = form.album.data.id
            if not form.album.data.sounds:
                rec.album_order = 0
            else:
                rec.album_order = form.album.data.sounds.count() + 1

        rec.user_id = current_user.id
        if not form.title.data:
            rec.title = filename_orig
        else:
            rec.title = form.title.data
        rec.description = form.description.data
        rec.private = form.private.data

        if "flac" in request.files["file"].mimetype or "ogg" in request.files["file"].mimetype:
            rec.transcode_state = Sound.TRANSCODE_WAITING
            rec.transcode_needed = True

        db.session.add(rec)
        db.session.commit()

        # push the job in queue
        from tasks import upload_workflow

        upload_workflow.delay(rec.id)

        # log
        add_user_log(rec.id, current_user.id, "sounds", "info", "Uploaded {0} -- {1}".format(rec.id, rec.title))

        return jsonify({"id": rec.flake_id, "slug": rec.slug})

    return jsonify({"error": json.dumps(form.errors)}), 400


@bp_api_tracks.route("/api/waveform/<string:username>/<string:soundslug>", methods=["GET"])
@require_oauth(None)
def waveform(username, soundslug):
    """
    Get track waveform.
    ---
    tags:
        - Tracks
    parameters:
        - name: username
          in: path
          type: string
          required: true
          description: User username
        - name: soundslug
          in: path
          type: string
          required: true
          description: Track slug
    responses:
        200:
            description: Returns the waveform datas.
    """
    # Get logged in user from bearer token, or None if not logged in
    current_user = current_token.user

    # Get the associated User from url fetch
    track_user = User.query.filter(User.name == username).first()
    if not track_user:
        return jsonify({"error": "User not found"}), 404

    sound = Sound.query.filter(Sound.slug == soundslug, Sound.user_id == track_user.id).first()
    if not sound:
        return jsonify({"error": "not found"}), 404

    if sound.private:
        if current_user:
            if sound.user_id != current_user.id:
                return jsonify({"error": "forbidden"}), 403
        else:
            return jsonify({"error": "forbidden"}), 403

    si = sound.sound_infos.first()
    if not si:
        return {"error": "not found"}, 404

    wf = json.loads(si.waveform)
    wf["filename"] = sound.path_sound()
    wf["wf_png"] = sound.path_waveform()
    wf["title"] = sound.title

    return jsonify(wf), 200


@bp_api_tracks.route("/api/tracks/<string:username>/<string:soundslug>", methods=["GET"])
@require_oauth(None)
def show(username, soundslug):
    """
    Get track details.
    ---
    tags:
        - Tracks
    parameters:
        - name: username
          in: path
          type: string
          required: true
          description: User username
        - name: soundslug
          in: path
          type: string
          required: true
          description: Track slug
    responses:
        200:
            description: Returns track details.
    """
    # Get logged in user from bearer token, or None if not logged in
    current_user = current_token.user

    # Get the associated User from url fetch
    track_user = User.query.filter(User.name == username).first()
    if not track_user:
        return jsonify({"error": "User not found"}), 404

    if current_user and track_user.id == current_user.id:
        sound = Sound.query.filter(Sound.slug == soundslug, Sound.user_id == track_user.id).first()
    else:
        sound = Sound.query.filter(
            Sound.slug == soundslug, Sound.user_id == track_user.id, Sound.transcode_state == Sound.TRANSCODE_DONE
        ).first()

    if not sound:
        return jsonify({"error": "not found"}), 404

    if sound.private:
        if current_user:
            if sound.user_id != current_user.id:
                return jsonify({"error": "forbidden"}), 403
        else:
            return jsonify({"error": "forbidden"}), 403

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
        "album_id": sound.album.flake_id,
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

    return jsonify(track_obj)


@bp_api_tracks.route("/api/tracks/<string:username>/<string:soundslug>", methods=["PATCH"])
@require_oauth("write")
def edit(username, soundslug):
    """
    Edit track.
    ---
    tags:
        - Tracks
    security:
        - OAuth2:
            - write
    parameters:
        - name: username
          in: path
          type: string
          required: true
          description: User username
        - name: soundslug
          in: path
          type: string
          required: true
          description: Track slug
    responses:
        200:
            description: Returns nothing.
    """
    current_user = current_token.user
    if not current_user:
        return jsonify({"error": "Unauthorized"}), 403

    # Get the track
    sound = Sound.query.filter(Sound.user_id == current_user.id, Sound.slug == soundslug).first()
    if not sound:
        return jsonify({"error": "Not found"}), 404

    return jsonify({"error": "Not implemented"}), 501


@bp_api_tracks.route("/api/tracks/<string:username>/<string:soundslug>", methods=["DELETE"])
@require_oauth("write")
def delete(username, soundslug):
    """
    Delete a track.
    ---
    tags:
        - Tracks
    security:
        - OAuth2:
            - write
    parameters:
        - name: username
          in: path
          type: string
          required: true
          description: User username
        - name: soundslug
          in: path
          type: string
          required: true
          description: Track slug
    responses:
        200:
            description: Returns nothing.
    """
    current_user = current_token.user
    if not current_user:
        return jsonify({"error": "Unauthorized"}), 403

    # Get the track
    sound = Sound.query.filter(Sound.user_id == current_user.id, Sound.slug == soundslug).first()
    if not sound:
        return jsonify({"error": "Not found"}), 404

    # Federate Delete
    from tasks import federate_delete_sound

    federate_delete_sound(sound)

    db.session.delete(sound)
    db.session.commit()

    # log
    add_user_log(sound.id, sound.user.id, "sounds", "info", "Deleted {0} -- {1}".format(sound.id, sound.title))

    return jsonify({}), 200
