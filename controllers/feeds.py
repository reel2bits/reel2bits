from werkzeug.contrib.atom import AtomFeed
from flask import Blueprint, request, url_for, abort, current_app, g
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

    feed_url = request.url
    url = f"https://{current_app.config['AP_DOMAIN']}/{user.name}"
    feed = AtomFeed(
        f"{user.name} tracks",
        feed_url=feed_url,
        url=url,
        subtitle=f"Tracks of {user.name}",
        logo=None or f"https://{current_app.config['AP_DOMAIN']}/static/userpic_placeholder.png",
        generator=("reel2bits", f"https://{current_app.config['AP_DOMAIN']}", g.cfg["REEL2BITS_VERSION"]),
        author={"name": user.name, "uri": f"https://{current_app.config['AP_DOMAIN']}/{user.name}"},
    )

    for track in q:
        url_transcode = url_for("get_uploads_stuff", thing="sounds", stuff=track.path_sound(orig=False), _external=True)
        feed.add(
            title=track.title,
            title_type="text",
            content=track.description,
            content_type="text",
            url=f"https://{current_app.config['AP_DOMAIN']}/{user.name}/{track.slug}",
            links=[{"href": url_transcode, "type": "audio/mpeg", "length": track.sound_infos.first().duration}],
            updated=track.updated,
            author={"name": user.name, "uri": f"https://{current_app.config['AP_DOMAIN']}/{user.name}"},
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

    feed_url = request.url
    url = f"https://{current_app.config['AP_DOMAIN']}/{user.name}"
    feed = AtomFeed(
        f"{album.title} by {user.name}",
        feed_url=feed_url,
        url=url,
        subtitle=f"Tracks for album '{album.title}' by {user.name}",
        logo=None or f"https://{current_app.config['AP_DOMAIN']}/static/artwork_placeholder.png",
        generator=("reel2bits", f"https://{current_app.config['AP_DOMAIN']}", g.cfg["REEL2BITS_VERSION"]),
        author={"name": user.name, "uri": f"https://{current_app.config['AP_DOMAIN']}/{user.name}"},
    )

    for track in album.sounds:
        url_transcode = url_for("get_uploads_stuff", thing="sounds", stuff=track.path_sound(orig=False), _external=True)
        feed.add(
            id=track.flake_id,
            title=track.title,
            title_type="text",
            content=track.description,
            content_type="text",
            url=f"https://{current_app.config['AP_DOMAIN']}/{user.name}/{track.slug}",
            links=[{"href": url_transcode, "type": "audio/mpeg", "length": track.sound_infos.first().duration}],
            updated=track.updated,
            author={"name": user.name, "uri": f"https://{current_app.config['AP_DOMAIN']}/{user.name}"},
            published=track.uploaded,
            rights=track.licence_info()["name"],
        )
    return feed.get_response()
