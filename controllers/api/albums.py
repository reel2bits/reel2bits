from flask import Blueprint, jsonify
from app_oauth import require_oauth
from authlib.flask.oauth2 import current_token
from forms import AlbumForm
from models import db, Album
import json
from utils import add_user_log

bp_api_albums = Blueprint("bp_api_albums", __name__)


@bp_api_albums.route("/api/albums/new", methods=["POST"])
@require_oauth("write")
def upload():
    current_user = current_token.user
    if not current_user:
        return jsonify({"error": "Unauthorized"}), 403

    form = AlbumForm()

    if form.validate_on_submit():
        rec = Album()
        rec.user_id = current_user.id
        rec.title = form.title.data
        rec.private = form.private.data
        rec.description = form.description.data

        db.session.add(rec)
        db.session.commit()

        # log
        add_user_log(rec.id, rec.user_id, "albums", "info", "Created {0} -- {1}".format(rec.id, rec.title))

        return jsonify({"id": rec.flake_id, "slug": rec.slug})

    return jsonify({"error": json.dumps(form.errors)}), 400
