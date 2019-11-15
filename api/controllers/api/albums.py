from flask import Blueprint, jsonify, request, current_app
from app_oauth import require_oauth
from authlib.flask.oauth2 import current_token
from forms import AlbumForm
from models import db, Album, User, Sound, SoundTag
import json
from utils.various import add_user_log, get_hashed_filename
from datas_helpers import to_json_relationship, to_json_account, to_json_album
from sqlalchemy import and_
from flask_uploads import UploadSet
from utils.defaults import Reel2bitsDefaults
import os


bp_api_albums = Blueprint("bp_api_albums", __name__)

artworkalbums = UploadSet("artworkalbums", Reel2bitsDefaults.artwork_extensions_allowed)


@bp_api_albums.route("/api/albums", methods=["POST"])
@require_oauth("write")
def new():
    """
    Create a new album.
    ---
    tags:
        - Albums
    security:
        - OAuth2:
            - write
    responses:
        200:
            description: Returns id and slug.
    """
    current_user = current_token.user
    if not current_user:
        return jsonify({"error": "Unauthorized"}), 403

    # Check artwork file size
    if "artwork" in request.files:
        artwork_uploaded = request.files["artwork"]
        artwork_uploaded.seek(0, os.SEEK_END)
        artwork_size = artwork_uploaded.tell()
        artwork_uploaded.seek(0)
        if artwork_size > Reel2bitsDefaults.artwork_size_limit:
            return jsonify({"error": "artwork too big, 2MB maximum"}), 413  # Request Entity Too Large
    else:
        artwork_uploaded = None

    form = AlbumForm()

    if form.validate_on_submit():
        rec = Album()
        rec.user_id = current_user.id
        rec.title = form.title.data
        rec.private = form.private.data
        rec.description = form.description.data
        rec.genre = form.genre.data

        # Save the artwork
        if artwork_uploaded:
            artwork_filename = get_hashed_filename(artwork_uploaded.filename)
            artworkalbums.save(artwork_uploaded, folder=current_user.slug, name=artwork_filename)
            rec.artwork_filename = artwork_filename

        # Handle tags
        tags = form.tags.data.split(",")
        # Clean
        tags = [t.strip() for t in tags if t]
        # For each tag get it or create it
        for tag in tags:
            dbt = SoundTag.query.filter(SoundTag.name == tag).first()
            if not dbt:
                dbt = SoundTag(name=tag)
                db.session.add(dbt)
            rec.tags.append(dbt)

        db.session.add(rec)
        db.session.commit()

        # log
        add_user_log(rec.id, rec.user_id, "albums", "info", "Created {0} -- {1}".format(rec.id, rec.title))

        return jsonify({"id": rec.flake_id, "slug": rec.slug})

    return jsonify({"error": json.dumps(form.errors)}), 400


@bp_api_albums.route("/api/albums/<string:username_or_id>/<string:albumslug>", methods=["GET"])
@require_oauth(optional=True)
def get(username_or_id, albumslug):
    """
    Get album details.
    ---
    tags:
        - Albums
    parameters:
        - name: user_id
          in: path
          type: integer
          required: true
          description: User ID
        - name: albumslug
          in: path
          type: string
          required: true
          description: Album slug
    responses:
        200:
            description: Returns album object.
    """
    # Get logged in user from bearer token, or None if not logged in
    if current_token:
        current_user = current_token.user
    else:
        current_user = None

    # Get the associated User from url fetch
    album_user = User.query.filter(User.flake_id == username_or_id).first()
    if not album_user:
        album_user = User.query.filter(User.name == username_or_id, User.local.is_(True)).first()
    if not album_user:
        return jsonify({"error": "User not found"}), 404

    if current_user and album_user.id == current_user.id:
        # we have a valid token, and album user is token user, can fetch private
        album = Album.query.filter(Album.slug == albumslug, Album.user_id == album_user.id).first()
    else:
        # only fetch public ones
        album = Album.query.filter(
            Album.slug == albumslug, Album.user_id == album_user.id, Album.private.is_(False)
        ).first()

    if not album:
        return jsonify({"error": "not found"}), 404

    if album.private:
        if current_user:
            if album.user_id != current_user.id:
                return jsonify({"error": "forbidden"}), 403
        else:
            return jsonify({"error": "forbidden"}), 403

    relationship = to_json_relationship(current_user, album.user)
    account = to_json_account(album.user, relationship)
    resp = to_json_album(album, account)

    return jsonify(resp)


@bp_api_albums.route("/api/albums/<string:username>/<string:albumslug>", methods=["DELETE"])
@require_oauth("write")
def delete(username, albumslug):
    """
    Delete album.
    ---
    tags:
        - Albums
    security:
        - OAuth2:
            - write
    parameters:
        - name: username
          in: path
          type: string
          required: true
          description: User username
        - name: albumslug
          in: path
          type: string
          required: true
          description: Album slug
    responses:
        200:
            description: Returns nothing.
    """
    current_user = current_token.user
    if not current_user:
        return jsonify({"error": "Unauthorized"}), 403

    # Get the track
    album = Album.query.filter(Album.user_id == current_user.id, Album.slug == albumslug).first()
    if not album:
        return jsonify({"error": "Not found"}), 404

    album_name = album.title

    db.session.delete(album)
    db.session.commit()

    # log
    add_user_log(album.id, album.user.id, "albums", "info", "Deleted {0} -- {1}".format(album.id, album.title))

    return jsonify(album_name), 200


@bp_api_albums.route("/api/albums/<string:username>/<string:albumslug>", methods=["PATCH"])
@require_oauth("write")
def edit(username, albumslug):
    """
    Edit album.
    ---
    tags:
        - Albums
    security:
        - OAuth2:
            - write
    parameters:
        - name: username
          in: path
          type: string
          required: true
          description: User username
        - name: albumslug
          in: path
          type: string
          required: true
          description: Album slug
    responses:
        200:
            description: Returns a Status with extra reel2bits params.
    """
    current_user = current_token.user
    if not current_user:
        return jsonify({"error": "Unauthorized"}), 403

    # Get the album
    album = Album.query.filter(Album.user_id == current_user.id, Album.slug == albumslug).first()
    if not album:
        return jsonify({"error": "Not found"}), 404

    description = request.json.get("description")
    private = request.json.get("private")
    title = request.json.get("title")
    genre = request.json.get("genre")
    tags = request.json.get("tags")

    if album.private and not private:
        return jsonify({"error": "Cannot change to private: album already federated"})

    if not title:
        return jsonify({"error": "Album title is required"}), 400

    album.title = title
    album.description = description
    album.genre = genre

    # First remove tags which have been removed
    for tag in album.tags:
        if tag.name not in tags:
            album.tags.remove(tag)

    # Then add the new ones if new
    for tag in tags:
        if tag not in [a.name for a in album.tags]:
            dbt = SoundTag.query.filter(SoundTag.name == tag).first()
            if not dbt:
                dbt = SoundTag(name=tag)
                db.session.add(dbt)
            album.tags.append(dbt)

    # Purge orphaned tags
    for otag in SoundTag.query.filter(and_(~SoundTag.sounds.any(), ~SoundTag.albums.any())).all():
        db.session.delete(otag)

    db.session.commit()

    relationship = False
    if current_token and current_token.user:
        relationship = to_json_relationship(current_token.user, album.user)
    account = to_json_account(album.user, relationship)
    return jsonify(to_json_album(album, account))


@bp_api_albums.route("/api/albums/<int:user_id>", methods=["GET"])
@require_oauth(optional=True)
def list(user_id):
    """
    Get album list.
    ---
    tags:
        - Albums
    parameters:
        - name: user_id
          in: path
          type: integer
          required: true
          description: User ID
        - name: short
          in: query
          type: boolean
          description: Short objects or full objects
    responses:
        200:
            description: Returns list of Albums.
    """
    # Get logged in user from bearer token, or None if not logged in
    if current_token:
        current_user = current_token.user
    else:
        current_user = None

    short_objects = request.args.get("short", False)
    count = int(request.args.get("count", 20))
    page = int(request.args.get("page", 1))

    q = current_user.albums

    if current_user.id != user_id:
        q = q.filter(Album.private.is_(False))

    q = q.order_by(Album.created.desc())

    if short_objects:
        albums = []
        for t in q.all():
            albums.append(
                {"id": t.id, "flake_id": t.flake_id, "title": t.title, "created": t.created, "private": t.private}
            )
        return jsonify(albums)
    else:
        q = q.paginate(page=page, per_page=count)

        albums = []
        for t in q.items:
            return jsonify({"error": "Non-short objects non implemented"}, 500)
        resp = {
            "page": page,
            "page_size": count,
            "totalItems": q.total,
            "items": albums,
            "totalPages": q.pages,
            "short": short_objects,
        }
        return jsonify(resp)


@bp_api_albums.route("/api/albums/<string:username>/<string:albumslug>/reorder", methods=["PATCH"])
@require_oauth("write")
def reorder(username, albumslug):
    """
    Edit album tracks order.
    ---
    tags:
        - Albums
    security:
        - OAuth2:
            - write
    responses:
        200:
            description: Returns a Status with extra reel2bits params.
    """
    current_user = current_token.user
    if not current_user:
        return jsonify({"error": "Unauthorized"}), 403

    # Get the album
    album = Album.query.filter(Album.user_id == current_user.id, Album.slug == albumslug).first()
    if not album:
        return jsonify({"error": "Not found"}), 404

    pos = 0
    for track in request.json:
        dbt = Sound.query.filter(Sound.flake_id == track["id"], Sound.album_id == album.id).first()
        if not dbt:
            return jsonify({"error": "Not found"}), 404
        dbt.album_order = pos
        pos += 1
    db.session.commit()

    relationship = to_json_relationship(current_user, album.user)
    account = to_json_account(album.user, relationship)
    resp = to_json_album(album, account)

    return jsonify(resp)


@bp_api_albums.route("/api/albums/<string:username>/<string:albumslug>/artwork", methods=["PATCH"])
@require_oauth("write")
def artwork(username, albumslug):
    """
    Change album artwork.
    ---
    tags:
        - Albums
    security:
        - OAuth2:
            - write
    parameters:
        - name: username
          in: path
          type: string
          required: true
          description: User username
        - name: albumslug
          in: path
          type: string
          required: true
          description: Album slug
    responses:
        200:
            description: Returns ok or not.
    """
    current_user = current_token.user
    if not current_user:
        return jsonify({"error": "Unauthorized"}), 403

    # Get the album
    album = Album.query.filter(Album.user_id == current_user.id, Album.slug == albumslug).first()
    if not album:
        return jsonify({"error": "Not found"}), 404

    # Check artwork file size
    if "artwork" not in request.files:
        return jsonify({"error": "Artwork file missing"}), 503

    artwork_uploaded = request.files["artwork"]
    artwork_uploaded.seek(0, os.SEEK_END)
    artwork_size = artwork_uploaded.tell()
    artwork_uploaded.seek(0)
    if artwork_size > Reel2bitsDefaults.artwork_size_limit:
        return jsonify({"error": "artwork too big, 2MB maximum"}), 413  # Request Entity Too Large

    # Delete old artwork if any
    if album.artwork_filename:
        old_artwork = os.path.join(current_app.config["UPLOADED_ARTWORKALBUMS_DEST"], album.path_artwork())
        if os.path.isfile(old_artwork):
            os.unlink(old_artwork)
        else:
            print(f"Error: cannot delete old artwork: {album.id} / {album.artwork_filename}")

    # Save new artwork
    artwork_filename = get_hashed_filename(artwork_uploaded.filename)
    artworkalbums.save(artwork_uploaded, folder=current_user.slug, name=artwork_filename)

    album.artwork_filename = artwork_filename

    db.session.commit()

    return jsonify({"status": "ok", "path": album.path_artwork()})
