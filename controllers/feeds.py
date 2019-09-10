from flask import Blueprint, request, url_for, abort, current_app, g
from models import User, Sound, Album
from feedgen.feed import FeedGenerator
import pytz

bp_feeds = Blueprint("bp_feeds", __name__)


def gen_feed(title, author, feed_url, url, subtitle, logo):
    fg = FeedGenerator()
    fg.load_extension("podcast")
    # fg.podcast.itunes_category('Technology', 'Podcasting')

    fg.id(feed_url)
    fg.title(title)
    fg.author(author)
    fg.link(href=url)
    fg.link(href=feed_url, rel="self")
    fg.logo(logo)
    fg.subtitle(subtitle)
    fg.language("en")
    fg.generator(
        generator="reel2bits", uri=f"https://{current_app.config['AP_DOMAIN']}", version=g.cfg["REEL2BITS_VERSION"]
    )
    return fg


def utcdate(date):
    return date.replace(tzinfo=pytz.utc)


@bp_feeds.route("/feeds/tracks/<int:user_id>", methods=["GET"])
@bp_feeds.route("/feeds/tracks/<int:user_id>.atom", methods=["GET"])
def tracks(user_id):
    user = User.query.filter(User.id == user_id).first()
    if not user:
        abort(404)

    q = Sound.query.filter(Sound.user_id == user.id, Sound.private.is_(False))
    q = q.filter(Sound.transcode_state == Sound.TRANSCODE_DONE)
    q = q.order_by(Sound.uploaded.desc())

    feed_url = request.url
    url = f"https://{current_app.config['AP_DOMAIN']}/{user.name}"
    author = {"name": user.name, "uri": f"https://{current_app.config['AP_DOMAIN']}/{user.name}"}
    logo = None or f"https://{current_app.config['AP_DOMAIN']}/static/userpic_placeholder.png"

    feed = gen_feed(f"{user.name} tracks", author, feed_url, url, f"Tracks of {user.name}", logo)

    for track in q:
        url_transcode = url_for("get_uploads_stuff", thing="sounds", stuff=track.path_sound(orig=False), _external=True)
        url = f"https://{current_app.config['AP_DOMAIN']}/{user.name}/track/{track.slug}"

        fe = feed.add_entry()
        fe.id(url)
        fe.title(track.title)
        fe.link(href=url)
        fe.enclosure(url_transcode, 0, "audio/mpeg")
        fe.description(track.description)
        fe.author({"name": user.name, "uri": f"https://{current_app.config['AP_DOMAIN']}/{user.name}"})
        fe.rights(track.licence_info()["name"])
        fe.pubdate(utcdate(track.uploaded))
        fe.updated(utcdate(track.updated))
        fe.content(track.description)
    return feed.atom_str(pretty=True)


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
    url = f"https://{current_app.config['AP_DOMAIN']}/{user.name}/album/{album.title}"
    author = {"name": user.name, "uri": f"https://{current_app.config['AP_DOMAIN']}/{user.name}"}
    logo = None or f"https://{current_app.config['AP_DOMAIN']}/static/artwork_placeholder.png"

    feed = gen_feed(
        f"{album.title} by {user.name}", author, feed_url, url, f"Tracks for album '{album.title}' by {user.name}", logo
    )

    for track in album.sounds.filter(Sound.transcode_state == Sound.TRANSCODE_DONE):
        url_transcode = url_for("get_uploads_stuff", thing="sounds", stuff=track.path_sound(orig=False), _external=True)
        url = f"https://{current_app.config['AP_DOMAIN']}/{user.name}/track/{track.slug}"

        fe = feed.add_entry()
        fe.id(url)
        fe.title(track.title)
        fe.link(href=url)
        fe.enclosure(url_transcode, 0, "audio/mpeg")
        fe.description(track.description)
        fe.author({"name": user.name, "uri": f"https://{current_app.config['AP_DOMAIN']}/{user.name}"})
        fe.rights(track.licence_info()["name"])
        fe.pubdate(utcdate(track.uploaded))
        fe.updated(utcdate(track.updated))
        fe.content(track.description)
    return feed.atom_str(pretty=True)
