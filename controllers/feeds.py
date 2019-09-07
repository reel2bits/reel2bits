from werkzeug.contrib.atom import AtomFeed
from flask import Blueprint, request, url_for, abort
from models import User, Sound, Album

bp_feeds = Blueprint("bp_feeds", __name__)


@bp_feeds.route("/feeds/tracks/<int:user_id>", methods=["GET"])
@bp_feeds.route("/feeds/tracks/<int:user_id>.atom", methods=["GET"])
def tracks(user_id):
    user = User.query.filter(User.id == user_id).first()
    if not user:
        abort(404)

    q = Sound.query.filter(Sound.user_id == user.id, Sound.private.is_(False))
    q = q.order_by(Sound.uploaded.desc())

    feed = AtomFeed(f"{user.name} tracks", feed_url=request.url, url=request.url_root)

    for track in q:
        url_transcode = url_for("get_uploads_stuff", thing="sounds", stuff=track.path_sound(orig=False), _external=True)
        feed.add(
            title=track.title,
            title_type="text",
            content=track.description,
            content_type="text",
            url=url_transcode,
            updated=track.updated,
            author=user.name,
            published=track.uploaded,
            rights=track.licence_info()["name"],
        )
    return feed.get_response()


@bp_feeds.route("/feeds/album/<int:user_id>/<int:album_id>", methods=["GET"])
@bp_feeds.route("/feeds/album/<int:user_id>/<int:album_id>.atom", methods=["GET"])
def album(user_id, album_id):
    user = User.query.filter(User.id == user_id).first()
    if not user:
        abort(404)
    album = Album.query.filter(Album.id == album_id, Album.user_id == user.id, Album.private.is_(False)).first()
    if not album:
        abort(404)

    feed = AtomFeed(f"{user.name} - {album.title}", feed_url=request.url, url=request.url_root)

    for track in album.sounds:
        url_transcode = url_for("get_uploads_stuff", thing="sounds", stuff=track.path_sound(orig=False), _external=True)
        feed.add(
            title=track.title,
            title_type="text",
            content=track.description,
            content_type="text",
            url=url_transcode,
            updated=track.updated,
            author=user.name,
            published=track.uploaded,
            rights=track.licence_info()["name"],
        )
    return feed.get_response()
