from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, json
from flask_babelex import gettext
from flask_security import login_required, current_user

from forms import AlbumForm
from models import db, User, Album, Sound
from utils.various import InvalidUsage, add_user_log

bp_albums = Blueprint("bp_albums", __name__)


@bp_albums.route("/user/<string:username>/sets/<string:setslug>/reorder.json", methods=["POST"])
def reorder_json(username, setslug):
    user = User.query.filter(User.name == username).first()
    if not user:
        raise InvalidUsage("User not found", status_code=404)

    album = Album.query.filter(Album.slug == setslug, Album.user_id == user.id).first()
    if not album:
        raise InvalidUsage("Album not found", status_code=404)

    if not current_user.is_authenticated:
        raise InvalidUsage("Login required", status_code=500)

    if user.id != current_user.id:
        raise InvalidUsage("Forbidden", status_code=500)

    if album.private:
        if current_user:
            if album.user_id != current_user.id:
                raise InvalidUsage("Album not found", status_code=404)
        else:
            raise InvalidUsage("Album not found", status_code=404)

    moved = []

    if not request.get_json():
        raise InvalidUsage("Invalid json", status_code=500)

    for snd in request.get_json()["data"]:
        sound = Sound.query.filter(Sound.id == int(snd["soundid"]), Sound.album_id == album.id).first()
        if not sound:
            raise InvalidUsage("Sound not found", status_code=404)

        if sound.album_order != int(snd["oldPosition"]):
            raise InvalidUsage(
                "Old position %s doesn't match bdd one %s" % (int(snd["oldPosition"]), sound.album_order)
            )
        sound.album_order = int(snd["newPosition"])

        moved.append(sound.id)

    db.session.commit()

    datas = {"status": "ok", "moved": moved}

    return Response(json.dumps(datas), mimetype="application/json;charset=utf-8")
