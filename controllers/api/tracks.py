from flask import Blueprint, request, jsonify
from app_oauth import require_oauth
from authlib.flask.oauth2 import current_token
from forms import SoundUploadForm
import json

bp_api_tracks = Blueprint("bp_api_tracks", __name__)


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
        return jsonify({'error': 'Unauthorized'}), 403

    if 'file' not in request.files:
        errors['file'] = "No file present"

    if len(errors) > 0:
        return jsonify({"error": errors}), 400

    form = SoundUploadForm()

    if form.validate_on_submit():
        return jsonify('I have no idea what to do'), 500

    return jsonify({'error': json.dumps(form.errors)}), 400
