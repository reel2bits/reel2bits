from flask import Blueprint, request, url_for, abort, current_app, g
from models import User, Sound, Album
from utils.defaults import Reel2bitsDefaults
from feedgen.feed import FeedGenerator
import pytz
import sqlalchemy

bp_feeds = Blueprint("bp_feeds", __name__)


def gen_feed(title, author, feed_url, url, subtitle, logo, categories=None, album=False, licenses=False, typ="atom"):
    fg = FeedGenerator()
    if typ != "rss":
        fg.load_extension("podcast")

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

    if album and categories and typ != "rss":
        fg.podcast.itunes_category(categories[0])
        fg.category([{"term": c, "label": c} for c in categories])

    if licenses:
        fg.rights("See individual tracks: " + ", ".join(licenses))

    print(typ)

    return fg


def utcdate(date):
    return date.replace(tzinfo=pytz.utc)


@bp_feeds.route("/feeds/tracks/<string:user_id>", methods=["GET"])
@bp_feeds.route("/feeds/tracks/<string:user_id>.atom", methods=["GET"], endpoint="tracks_atom")
@bp_feeds.route("/feeds/tracks/<string:user_id>.rss", methods=["GET"], endpoint="tracks_rss")
def tracks(user_id):
    try:
        user = User.query.filter(User.flake_id == user_id).first()
    except sqlalchemy.exc.DataError:
        abort(500)
    if not user:
        abort(404)

    typ = "rss" if request.endpoint in ["bp_feeds.tracks_rss"] else "atom"

    q = Sound.query.filter(Sound.user_id == user.id, Sound.private.is_(False))
    q = q.filter(Sound.transcode_state == Sound.TRANSCODE_DONE)
    q = q.order_by(Sound.uploaded.desc())

    feed_url = request.url
    url = f"https://{current_app.config['AP_DOMAIN']}/{user.name}"
    author = {"name": user.name, "uri": f"https://{current_app.config['AP_DOMAIN']}/{user.name}"}
    logo = None or f"https://{current_app.config['AP_DOMAIN']}/static/userpic_placeholder.png"

    feed = gen_feed(f"{user.name} tracks", author, feed_url, url, f"Tracks of {user.name}", logo, typ=typ)

    for track in q:
        path_sound = track.path_sound(orig=False)
        if not path_sound:
            continue
        url_transcode = url_for("get_uploads_stuff", thing="sounds", stuff=path_sound, _external=False)
        url = f"https://{current_app.config['AP_DOMAIN']}/{user.name}/track/{track.slug}"

        fe = feed.add_entry()
        fe.id(url)
        fe.title(track.title)
        fe.link(href=url)
        fe.enclosure(url_transcode, 0, "audio/mpeg")
        fe.description(track.description)
        fe.author({"name": user.name, "uri": f"https://{current_app.config['AP_DOMAIN']}/{user.name}"})
        fe.rights(track.licence_info()["name"])
        fe.pubDate(utcdate(track.uploaded))
        fe.updated(utcdate(track.updated))
        fe.content(track.description)
    if typ == "rss":
        return feed.rss_str(pretty=True)
    else:
        return feed.atom_str(pretty=True)


@bp_feeds.route("/feeds/album/<string:user_id>/<int:album_id>", methods=["GET"])
@bp_feeds.route("/feeds/album/<string:user_id>/<int:album_id>.atom", methods=["GET"], endpoint="album_atom")
@bp_feeds.route("/feeds/album/<string:user_id>/<int:album_id>.rss", methods=["GET"], endpoint="album_rss")
def album(user_id, album_id):
    try:
        user = User.query.filter(User.flake_id == user_id).first()
    except sqlalchemy.exc.DataError:
        abort(500)
    if not user:
        abort(404)
    try:
        album = Album.query.filter(Album.id == album_id, Album.user_id == user.id, Album.private.is_(False)).first()
    except sqlalchemy.exc.DataError:
        abort(500)
    if not album:
        abort(404)

    typ = "rss" if request.endpoint in ["bp_feeds.album_rss"] else "atom"

    feed_url = request.url
    url = f"https://{current_app.config['AP_DOMAIN']}/{user.name}/album/{album.title}"
    author = {"name": user.name, "uri": f"https://{current_app.config['AP_DOMAIN']}/{user.name}"}

    if album.path_artwork():
        logo = url_for("get_uploads_stuff", thing="artwork_albums", stuff=album.path_artwork(), _external=True)
    else:
        logo = None

    categories = [album.genre]

    licenses = album.sounds.with_entities(Sound.licence).group_by(Sound.licence).all()
    lics = []
    for lic in licenses:
        lic_infos = Reel2bitsDefaults.known_licences[lic.licence]
        if lic_infos:
            lics.append(lic_infos["name"])

    feed = gen_feed(
        f"{album.title} by {user.name}",
        author,
        feed_url,
        url,
        f"Tracks for album '{album.title}' by {user.name}",
        logo,
        categories=categories,
        album=True,
        licenses=lics,
        typ=typ,
    )

    for track in album.sounds.filter(Sound.transcode_state == Sound.TRANSCODE_DONE):
        path_sound = track.path_sound(orig=False)
        if not path_sound:
            continue
        url_transcode = url_for("get_uploads_stuff", thing="sounds", stuff=path_sound, _external=False)
        url = f"https://{current_app.config['AP_DOMAIN']}/{user.name}/track/{track.slug}"

        fe = feed.add_entry()
        fe.id(url)
        fe.title(track.title)
        fe.link(href=url)
        fe.enclosure(url_transcode, 0, "audio/mpeg")
        fe.description(track.description)
        fe.author({"name": user.name, "uri": f"https://{current_app.config['AP_DOMAIN']}/{user.name}"})
        fe.rights(track.licence_info()["name"])
        fe.pubDate(utcdate(track.uploaded))
        fe.updated(utcdate(track.updated))
        fe.content(track.description)
        fe.category([{"term": c, "label": c} for c in [track.genre]])
    if typ == "rss":
        return feed.rss_str(pretty=True)
    else:
        return feed.atom_str(pretty=True)
