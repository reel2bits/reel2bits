from flask import Blueprint, request, jsonify, current_app, url_for
from app_oauth import require_oauth
from authlib.flask.oauth2 import current_token
from forms import SoundUploadForm
from models import db, Sound, User
import json
from utils import add_user_log, get_hashed_filename
from flask_uploads import UploadSet, AUDIO

bp_api_tracks = Blueprint("bp_api_tracks", __name__)

sounds = UploadSet("sounds", AUDIO)


@bp_api_tracks.route("/api/tracks/upload", methods=["POST"])
@require_oauth("write")
def upload():
    """
    Upload a track
    :return: JSON
    """
    errors = {}

    user = current_token.user
    if not user:
        return jsonify({"error": "Unauthorized"}), 403

    if "file" not in request.files:
        errors["file"] = "No file present"

    if len(errors) > 0:
        return jsonify({"error": errors}), 400

    form = SoundUploadForm()

    if form.validate_on_submit():
        filename_orig = request.files["file"].filename
        filename_hashed = get_hashed_filename(filename_orig)

        sounds.save(request.files["file"], folder=user.slug, name=filename_hashed)

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

        rec.user_id = user.id
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
        add_user_log(rec.id, user.id, "sounds", "info", "Uploaded {0} -- {1}".format(rec.id, rec.title))

        return jsonify({"id": rec.flake_id, "slug": rec.slug})

    return jsonify({"error": json.dumps(form.errors)}), 400


@bp_api_tracks.route("/api/tracks/get/<string:username>/<string:soundslug>", methods=["GET"])
@require_oauth(None)
def show(username, soundslug):
    # Get logged in user from bearer token, or None if not logged in
    current_user = current_token.user

    # Get the associated User from url fetch
    track_user = User.query.filter(User.name == username).first()
    if not track_user:
        return jsonify({'error': 'User not found'}), 404

    if current_user and track_user.id == current_user.id:
        sound = Sound.query.filter(Sound.slug == soundslug, Sound.user_id == track_user.id).first()
    else:
        sound = Sound.query.filter(
            Sound.slug == soundslug, Sound.user_id == track_user.id, Sound.transcode_state == Sound.TRANSCODE_DONE
        ).first()

    if sound.private:
        if current_user:
            if sound.user_id != current_user.id:
                return jsonify({'error': 'forbidden'}), 403
        else:
            return jsonify({'error': 'forbidden'}), 403

    si = sound.sound_infos.first()

    url_orig = url_for('get_uploads_stuff', thing='sounds', stuff=sound.path_sound(orig=True))
    url_transcode = url_for('get_uploads_stuff', thing='sounds', stuff=sound.path_sound(orig=False))

    track_obj = {
        'id': sound.flake_id,
        'title': sound.title,
        'user': sound.user.name,
        'description': sound.description,
        'picture_url': None,  # FIXME not implemented yet
        'media_orig': url_orig,
        'media_transcoded': url_transcode,
        'waveform': (si.waveform if si else None),
        'private': sound.private,
        'uploaded_on': sound.uploaded,
        'uploaded_elapsed': sound.elapsed(),
        'album_id': None,  # FIXME not implemented yet, needs album flake id
        'processing': {
            'basic': (si.done_basic if si else None),
            'transcode_state': sound.transcode_state,
            'transcode_needed': sound.transcode_needed,
            'done': sound.processing_done()
        },
        'metadatas': {
            'licence': (sound.licence),
            'duration': (si.duration if si else None),
            'type': (si.type if si else None),
            'codec': (si.codec if si else None),
            'format': (si.format if si else None),
            'channels': (si.channels if si else None),
            'rate': (si.rate if si else None)  # Hz
        }
    }
    if si:
        if si.bitrate and si.bitrate_mode:
            track_obj['metadatas']['bitrate'] = si.bitrate
            track_obj['metadatas']['bitrate_mode'] = si.bitrate_mode

    return jsonify(track_obj)
