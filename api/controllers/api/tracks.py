from flask import Blueprint, request, jsonify, current_app
from app_oauth import require_oauth
from authlib.flask.oauth2 import current_token
from forms import SoundUploadForm
from models import db, Sound, User, Album, UserLogging, SoundTag
import json
from utils.various import add_user_log, get_hashed_filename
from flask_uploads import UploadSet, AUDIO
from datas_helpers import to_json_track, to_json_account, to_json_relationship
from os.path import splitext
import os
from sqlalchemy import and_
from utils.defaults import Reel2bitsDefaults
from tasks import send_update_sound
import sqlalchemy.exc


bp_api_tracks = Blueprint("bp_api_tracks", __name__)

sounds = UploadSet("sounds", AUDIO)
artworksounds = UploadSet("artworksounds", Reel2bitsDefaults.artwork_extensions_allowed)


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

    if not current_token.user:
        return jsonify({"error": "Unauthorized"}), 403
    current_user = User.query.filter(User.id == current_token.user.id).one()

    if "file" not in request.files:
        errors["file"] = "No file present"

    if len(errors) > 0:
        return jsonify({"error": errors}), 400

    # Check for user quota already reached
    if current_user.quota_count >= current_user.quota:
        return jsonify({"error": "quota limit reached"}), 507  # Insufficient storage
        # or 509 Bandwitdh Limit Exceeded...

    # Get file, and file size
    file_uploaded = request.files["file"]
    file_uploaded.seek(0, os.SEEK_END)  # ff to the end
    file_size = file_uploaded.tell()
    file_uploaded.seek(0)  # rewind

    if (current_user.quota_count + file_size) > current_user.quota:
        return jsonify({"error": "quota limit reached"}), 507  # Insufficient storage

    # Do the same with the artwork
    if "artwork" in request.files:
        artwork_uploaded = request.files["artwork"]
        artwork_uploaded.seek(0, os.SEEK_END)
        artwork_size = artwork_uploaded.tell()
        artwork_uploaded.seek(0)
        if artwork_size > Reel2bitsDefaults.artwork_size_limit:  # Max size of 2MB
            return jsonify({"error": "artwork too big, 2MB maximum"}), 413  # Request Entity Too Large
    else:
        artwork_uploaded = None

    form = SoundUploadForm()

    if form.validate_on_submit():
        filename_orig = file_uploaded.filename
        filename_hashed = get_hashed_filename(filename_orig)

        # Save the track file
        sounds.save(file_uploaded, folder=current_user.slug, name=filename_hashed)

        rec = Sound()
        rec.filename = filename_hashed
        rec.filename_orig = filename_orig

        # Save the artwork
        if artwork_uploaded:
            artwork_filename = get_hashed_filename(artwork_uploaded.filename)
            artworksounds.save(artwork_uploaded, folder=current_user.slug, name=artwork_filename)
            rec.artwork_filename = artwork_filename

        rec.licence = form.licence.data
        if form.album.data:
            rec.album_id = form.album.data.id
            if not form.album.data.sounds:
                rec.album_order = 0
            else:
                rec.album_order = form.album.data.sounds.count() + 1

        rec.user_id = current_user.id
        if not form.title.data:
            rec.title, _ = splitext(filename_orig)
        else:
            rec.title = form.title.data
        rec.description = form.description.data
        rec.private = form.private.data
        rec.file_size = file_size
        rec.transcode_file_size = 0  # will be filled, if needed in transcoding workflow
        rec.genre = form.genre.data

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

        if "flac" in file_uploaded.mimetype or "ogg" in file_uploaded.mimetype or "wav" in file_uploaded.mimetype:
            rec.transcode_state = Sound.TRANSCODE_WAITING
            rec.transcode_needed = True

        db.session.add(rec)

        # recompute user quota
        current_user.quota_count = current_user.quota_count + rec.file_size

        db.session.commit()

        # push the job in queue
        from tasks import upload_workflow

        upload_workflow.delay(rec.id)

        # log
        add_user_log(rec.id, current_user.id, "sounds", "info", "Uploaded {0} -- {1}".format(rec.id, rec.title))

        return jsonify({"id": rec.flake_id, "slug": rec.slug})

    return jsonify({"error": json.dumps(form.errors)}), 400


@bp_api_tracks.route("/api/tracks/<string:username_or_id>/<string:soundslug>", methods=["GET"])
@require_oauth(optional=True)
def show(username_or_id, soundslug):
    """
    Get track details.
    ---
    tags:
        - Tracks
    parameters:
        - name: user_id
          in: path
          type: integer
          required: true
          description: User ID
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
    if current_token:
        current_user = User.query.filter(User.id == current_token.user.id).one()
    else:
        current_user = None

    # Get the associated User from url fetch
    track_user = User.query.filter(User.name == username_or_id, User.local.is_(True)).first()
    if not track_user:
        try:
            track_user = User.query.filter(User.flake_id == username_or_id).first()
        except sqlalchemy.exc.DataError:
            return jsonify({"error": "User not found"}), 404
    if not track_user:
        return jsonify({"error": "User not found"}), 404

    if current_user and (track_user.id == current_user.id):
        print("user")
        sound = Sound.query.filter(Sound.slug == soundslug, Sound.user_id == track_user.id).first()
    else:
        print("no user")
        sound = Sound.query.filter(
            Sound.slug == soundslug, Sound.user_id == track_user.id, Sound.transcode_state == Sound.TRANSCODE_DONE
        ).first()

    if not sound:
        print("mmmh")
        return jsonify({"error": "not found"}), 404

    if sound.private:
        if current_user:
            if sound.user_id != current_user.id:
                return jsonify({"error": "forbidden"}), 403
        else:
            return jsonify({"error": "forbidden"}), 403

    relationship = False
    if current_token and current_token.user:
        relationship = to_json_relationship(current_token.user, sound.user)
    account = to_json_account(sound.user, relationship)
    return jsonify(to_json_track(sound, account))


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
            description: Returns a Status with extra reel2bits params.
    """
    if not current_token.user:
        return jsonify({"error": "Unauthorized"}), 403
    current_user = User.query.filter(User.id == current_token.user.id).one()

    # Get the track
    sound = Sound.query.filter(Sound.user_id == current_user.id, Sound.slug == soundslug).first()
    if not sound:
        return jsonify({"error": "Not found"}), 404

    album = request.json.get("album")
    description = request.json.get("description")
    licence = request.json.get("licence")
    private = request.json.get("private")
    title = request.json.get("title")
    genre = request.json.get("genre")
    tags = request.json.get("tags")

    if sound.private and not private:
        return jsonify({"error": "Cannot change to private: track already federated"})

    if not title:
        title, _ = splitext(sound.filename_orig)
    else:
        sound.title = title

    sound.description = description
    sound.licence = licence
    sound.genre = genre

    # First remove tags which have been removed
    for tag in sound.tags:
        if tag.name not in tags:
            sound.tags.remove(tag)

    # Then add the new ones if new
    for tag in tags:
        if tag not in [a.name for a in sound.tags]:
            dbt = SoundTag.query.filter(SoundTag.name == tag).first()
            if not dbt:
                dbt = SoundTag(name=tag)
                db.session.add(dbt)
            sound.tags.append(dbt)

    # Purge orphaned tags
    for otag in SoundTag.query.filter(and_(~SoundTag.sounds.any(), ~SoundTag.albums.any())).all():
        db.session.delete(otag)

    # Fetch album, and associate if owner
    if album and (album != "__None"):
        db_album = Album.query.filter(Album.id == album).first()
        if db_album and (db_album.user_id == current_user.id):
            sound.album_id = db_album.id
            if not db_album.sounds:
                sound.album_order = 0
            else:
                sound.album_order = db_album.sounds.count() + 1
    elif album == "__None":
        sound.album_id = None
        sound.album_order = 0

    db.session.commit()

    # trigger a sound update
    send_update_sound(sound)

    relationship = False
    if current_token and current_token.user:
        relationship = to_json_relationship(current_token.user, sound.user)
    account = to_json_account(sound.user, relationship)
    return jsonify(to_json_track(sound, account))


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
            description: Returns track name.
    """
    if not current_token.user:
        return jsonify({"error": "Unauthorized"}), 403
    current_user = User.query.filter(User.id == current_token.user.id).one()

    # Get the track
    sound = Sound.query.filter(Sound.user_id == current_user.id, Sound.slug == soundslug).first()
    if not sound:
        return jsonify({"error": "Not found"}), 404

    track_name = sound.title
    freed_space = sound.file_size + sound.transcode_file_size

    # Federate Delete
    from tasks import federate_delete_sound

    federate_delete_sound(sound)

    db.session.delete(sound)

    # recompute user quota
    current_user.quota_count = current_user.quota_count - freed_space

    db.session.commit()

    # log
    add_user_log(sound.id, sound.user.id, "sounds", "info", "Deleted {0} -- {1}".format(sound.id, sound.title))

    return jsonify(track_name), 200


@bp_api_tracks.route("/api/tracks/<string:username_or_id>/<string:soundslug>/logs", methods=["GET"])
@require_oauth("read")
def logs(username_or_id, soundslug):
    """
    Get track logs.
    ---
    tags:
        - Tracks
    parameters:
        - name: user_id
          in: path
          type: integer
          required: true
          description: User ID
        - name: soundslug
          in: path
          type: string
          required: true
          description: Track slug
    responses:
        200:
            description: Returns track logs.
    """
    # Get logged in user from bearer token, or None if not logged in
    if current_token:
        current_user = User.query.filter(User.id == current_token.user.id).one()
    else:
        current_user = None

    # Get the associated User from url fetch
    track_user = User.query.filter(User.name == username_or_id, User.local.is_(True)).first()
    if not track_user:
        try:
            track_user = User.query.filter(User.flake_id == username_or_id).first()
        except sqlalchemy.exc.DataError:
            return jsonify({"error": "User not found"}), 404
    if not track_user:
        return jsonify({"error": "User not found"}), 404

    if current_user and (track_user.id == current_user.id):
        print("user")
        sound = Sound.query.filter(Sound.slug == soundslug, Sound.user_id == track_user.id).first()
    else:
        print("no user")
        sound = Sound.query.filter(
            Sound.slug == soundslug, Sound.user_id == track_user.id, Sound.transcode_state == Sound.TRANSCODE_DONE
        ).first()

    if not sound:
        print("mmmh")
        return jsonify({"error": "not found"}), 404

    if sound.private:
        if current_user:
            if sound.user_id != current_user.id:
                return jsonify({"error": "forbidden"}), 403
        else:
            return jsonify({"error": "forbidden"}), 403

    user_logs = UserLogging.query.filter(
        UserLogging.user_id == current_user.id, UserLogging.category == "sounds", UserLogging.item_id == sound.id
    ).all()

    logs = []
    for log in user_logs:
        logs.append({"message": log.message, "date": log.timestamp, "level": log.level})

    logs = {"trackSlug": sound.slug, "logs": logs}
    return jsonify(logs)


@bp_api_tracks.route("/api/tracks/<string:username_or_id>/<string:soundslug>/retry_processing", methods=["POST"])
@require_oauth("write")
def retry_processing(username_or_id, soundslug):
    """
    Reset track processing state.
    ---
    tags:
        - Tracks
    parameters:
        - name: user_id
          in: path
          type: integer
          required: true
          description: User ID
        - name: soundslug
          in: path
          type: string
          required: true
          description: Track slug
    responses:
        200:
            description: Returns track id.
    """
    # Get logged in user from bearer token, or None if not logged in
    if current_token:
        current_user = User.query.filter(User.id == current_token.user.id).one()
    else:
        current_user = None

    if not current_user:
        return jsonify({"error": "unauthorized"}), 401

    # Get the associated User from url fetch
    track_user = User.query.filter(User.name == username_or_id, User.local.is_(True)).first()
    if not track_user:
        try:
            track_user = User.query.filter(User.flake_id == username_or_id).first()
        except sqlalchemy.exc.DataError:
            return jsonify({"error": "User not found"}), 404
    if not track_user:
        return jsonify({"error": "User not found"}), 404

    if current_user.id != track_user.id:
        return jsonify({"error": "forbidden"}), 403

    sound = Sound.query.filter(Sound.slug == soundslug, Sound.user_id == track_user.id).first()
    if not sound:
        return jsonify({"error": "not found"}), 404

    if sound.transcode_state != Sound.TRANSCODE_ERROR:
        return jsonify({"error": "cannot reset transcode state if no error"}), 503

    # Delete sound info if any
    if sound.sound_infos.count() > 0:
        db.session.delete(sound.sound_infos.one())

    # Reset transcode state if transcode is needed
    if sound.transcode_needed:
        sound.transcode_state = Sound.TRANSCODE_WAITING

    db.session.commit()

    # re-schedule a job push
    from tasks import upload_workflow

    upload_workflow.delay(sound.id)

    # log
    add_user_log(
        sound.id,
        current_user.id,
        "sounds",
        "info",
        "Re-scheduled a processing {0} -- {1}".format(sound.id, sound.title),
    )

    return jsonify({"trackId": sound.id})


@bp_api_tracks.route("/api/tracks/<string:username>/<string:trackslug>/artwork", methods=["PATCH"])
@require_oauth("write")
def artwork(username, trackslug):
    """
    Change track artwork.
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
        - name: trackslug
          in: path
          type: string
          required: true
          description: Track slug
    responses:
        200:
            description: Returns ok or not.
    """
    if not current_token.user:
        return jsonify({"error": "Unauthorized"}), 403
    current_user = User.query.filter(User.id == current_token.user.id).one()

    # Get the track
    track = Sound.query.filter(Sound.user_id == current_user.id, Sound.slug == trackslug).first()
    if not track:
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
    if track.artwork_filename:
        old_artwork = os.path.join(current_app.config["UPLOADED_ARTWORKSOUNDS_DEST"], track.path_artwork())
        if os.path.isfile(old_artwork):
            os.unlink(old_artwork)
        else:
            print(f"Error: cannot delete old track artwork: {track.id} / {track.artwork_filename}")

    # Save new artwork
    artwork_filename = get_hashed_filename(artwork_uploaded.filename)
    artworksounds.save(artwork_uploaded, folder=current_user.slug, name=artwork_filename)

    track.artwork_filename = artwork_filename

    db.session.commit()

    # trigger a sound update
    send_update_sound(track)

    return jsonify({"status": "ok", "path": track.path_artwork()})
