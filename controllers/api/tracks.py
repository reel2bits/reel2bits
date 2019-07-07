from flask import Blueprint, request, jsonify
from app_oauth import require_oauth
from authlib.flask.oauth2 import current_token
from forms import SoundUploadForm
from models import db, Sound
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
