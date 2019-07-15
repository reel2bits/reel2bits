from flask import Blueprint, jsonify
from app_oauth import require_oauth
from authlib.flask.oauth2 import current_token
from forms import AlbumForm
from models import db, Album, User
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


@bp_api_albums.route("/api/albums/get/<string:username>/<string:albumslug>", methods=["GET"])
@require_oauth(None)
def show(username, albumslug):
    # Get logged in user from bearer token, or None if not logged in
    current_user = current_token.user

    # Get the associated User from url fetch
    album_user = User.query.filter(User.name == username).first()
    if not album_user:
        print("User not found")
        return jsonify({"error": "User not found"}), 404

    if current_user and album_user.id == current_user.id:
        album = Album.query.filter(Album.slug == albumslug, Album.user_id == album_user.id).first()

    if not album:
        return jsonify({"error": "not found"}), 404

    if album.private:
        if current_user:
            if album.user_id != current_user.id:
                return jsonify({"error": "forbidden"}), 403
        else:
            return jsonify({"error": "forbidden"}), 403

    album_obj = {
        "id": album.flake_id,
        "title": album.title,
        "created": album.created,
        "updated": album.updated,
        "description": album.description,
        "private": album.private,
        "slug": album.slug,
        "user_id": album.user_id,
        "user": album.user.name,
        "sounds": album.sounds.all(),
        "timeline": album.timeline,
    }

    return jsonify(album_obj)


@bp_api_albums.route("/api/albums/delete/<string:username>/<string:albumslug>", methods=["DELETE"])
@require_oauth("write")
def delete(username, albumslug):
    current_user = current_token.user
    if not current_user:
        return jsonify({"error": "Unauthorized"}), 403

    # Get the track
    album = Album.query.filter(Album.user_id == current_user.id, Album.slug == albumslug).first()
    if not album:
        return jsonify({"error": "Not found"}), 404

    db.session.delete(album)
    db.session.commit()

    # log
    add_user_log(album.id, album.user.id, "albums", "info", "Deleted {0} -- {1}".format(album.id, album.title))

    return jsonify({}), 200
