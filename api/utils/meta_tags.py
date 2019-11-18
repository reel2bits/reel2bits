from flask import current_app, url_for
from models import Config, User, Sound, Album
from utils.various import join_url
from werkzeug.routing import RequestRedirect, MethodNotAllowed, NotFound
import urllib.parse


def get_view_info(url, method="GET", environ=None):
    """Match a url and return the view and arguments
    it will be called with, or None if there is no view.
    """

    if environ:
        adapter = current_app.url_map.bind_to_environ(environ)
    else:
        adapter = current_app.url_map.bind("localhost")

    try:
        match = adapter.match(url, method=method)
    except RequestRedirect as e:
        # recursively match redirects
        return get_view_info(e.new_url, method)
    except (MethodNotAllowed, NotFound):
        # no match
        return None

    try:
        return match
    except KeyError:
        # no view is associated with the endpoint
        return None


def get_default_head_tags(path):
    _config = Config.query.first()
    if not _config:
        return []

    instance_name = _config.app_name
    short_description = _config.app_description
    app_name = "reel2bits"

    parts = [instance_name, app_name]

    return [
        {"tag": "meta", "property": "og:type", "content": "website"},
        {"tag": "meta", "property": "og:site_name", "content": " - ".join([p for p in parts if p])},
        {"tag": "meta", "property": "og:description", "content": short_description},
        {
            "tag": "meta",
            "property": "og:image",
            "content": join_url(current_app.config["REEL2BITS_URL"], "/static/favicon.png"),
        },
        {"tag": "meta", "property": "og:url", "content": join_url(current_app.config["REEL2BITS_URL"], path)},
    ]


def get_twitter_card_metas(type, id):
    embed_url = url_for("bp_api_embed.iframe", kind=type, id=id, _external=True)
    return [
        {"tag": "meta", "property": "twitter:card", "content": "player"},
        {"tag": "meta", "property": "twitter:player", "content": embed_url},
        {"tag": "meta", "property": "twitter:player:width", "content": "600"},
        {"tag": "meta", "property": "twitter:player:height", "content": "400"},
    ]


def get_user(view_arguments):
    return User.query.filter(User.name == view_arguments["username"], User.local.is_(True)).first()


def get_user_track_tags(view_name, view_arguments):
    user = get_user(view_arguments)
    if not user:
        return []
    track = Sound.query.filter(
        Sound.slug == view_arguments["trackslug"],
        Sound.user_id == user.id,
        Sound.private.is_(False),
        Sound.transcode_state == Sound.TRANSCODE_DONE,
    ).first()
    if not track:
        return []

    track_url = url_for("bp_spa.user_track", username=user.name, trackslug=user.name, _external=True)
    musician_url = url_for("bp_spa.user_profile", username=user.name, _external=True)
    path_sound = track.path_sound(orig=False)
    if not path_sound:
        return []
    transcode_url = url_for("get_uploads_stuff", thing="sounds", stuff=path_sound, _external=True)

    metas = [
        {"tag": "meta", "property": "og:url", "content": track_url},
        {"tag": "meta", "property": "og:title", "content": track.title},
        {"tag": "meta", "property": "og:type", "content": "music.song"},
        {"tag": "meta", "property": "music:musician", "content": musician_url},
    ]

    if track.album:
        album_url = url_for("bp_spa.user_album", username=user.name, albumslug=track.album.slug, _external=True)
        metas.append({"tag": "meta", "property": "music:album:disc", "content": 1})
        metas.append({"tag": "meta", "property": "music:album:track", "content": track.album_order})
        metas.append({"tag": "meta", "property": "music:album", "content": album_url})
    if track.artwork_filename:
        url_artwork = url_for("get_uploads_stuff", thing="artwork_sounds", stuff=track.path_artwork(), _external=True)
    else:
        url_artwork = join_url(current_app.config["REEL2BITS_URL"], "/static/artwork_placeholder.png")
    metas.append({"tag": "meta", "property": "og:image", "content": url_artwork})
    metas.append({"tag": "meta", "property": "og:audio", "content": transcode_url})

    oembed_url = join_url(
        current_app.config["REEL2BITS_URL"], f"/api/oembed?format=json&url={urllib.parse.quote_plus(track_url)}"
    )

    metas.append({"tag": "link", "rel": "alternate", "type": "application/json+oembed", "href": oembed_url})

    metas += get_twitter_card_metas(type="track", id=track.id)

    return metas


def get_user_album_tags(view_name, view_arguments):
    user = get_user(view_arguments)
    if not user:
        return []

    album = Album.query.filter(
        Album.user_id == user.id, Album.private.is_(False), Album.slug == view_arguments["albumslug"]
    ).first()
    if not album:
        return []

    album_url = url_for("bp_spa.user_album", username=user.name, albumslug=album.slug, _external=True)
    musician_url = url_for("bp_spa.user_profile", username=user.name, _external=True)
    feed_url = url_for("bp_feeds.album", user_id=album.user.id, album_id=album.id, _external=True)

    metas = [
        {"tag": "meta", "property": "og:url", "content": album_url},
        {"tag": "meta", "property": "og:title", "content": album.title},
        {"tag": "meta", "property": "og:type", "content": "music.album"},
        {"tag": "meta", "property": "music:musician", "content": musician_url},
        {"tag": "link", "rel": "alternate", "type": "application/atom+xml", "href": feed_url},
    ]

    if album.artwork_filename:
        url_artwork = url_for("get_uploads_stuff", thing="artwork_albums", stuff=album.path_artwork(), _external=True)
    else:
        url_artwork = join_url(current_app.config["REEL2BITS_URL"], "/static/artwork_placeholder.png")
    metas.append({"tag": "meta", "property": "og:image", "content": url_artwork})

    oembed_url = join_url(
        current_app.config["REEL2BITS_URL"], f"/api/oembed?format=json&url={urllib.parse.quote_plus(album_url)}"
    )

    metas.append({"tag": "link", "rel": "alternate", "type": "application/json+oembed", "href": oembed_url})

    metas += get_twitter_card_metas(type="album", id=album.id)

    return metas


def get_user_profile_tags(view_name, view_arguments):
    user = get_user(view_arguments)
    if not user:
        return []

    feed_url = url_for("bp_feeds.tracks", user_id=user.id, _external=True)
    musician_url = url_for("bp_spa.user_profile", username=user.name, _external=True)

    metas = [
        {"tag": "link", "rel": "alternate", "type": "application/atom+xml", "href": feed_url},
        {"tag": "meta", "property": "og:url", "content": musician_url},
        {"tag": "meta", "property": "og:title", "content": user.name},
        {"tag": "meta", "property": "og:type", "content": "profile"},
    ]

    if user.avatar_filename:
        url_avatar = url_for("get_uploads_stuff", thing="avatars", stuff=user.path_avatar(), _external=True)
    else:
        url_avatar = join_url(current_app.config["REEL2BITS_URL"], "/static/userpic_placeholder.png")
    metas.append({"tag": "meta", "property": "og:image", "content": url_avatar})

    oembed_url = join_url(
        current_app.config["REEL2BITS_URL"], f"/api/oembed?format=json&url={urllib.parse.quote_plus(musician_url)}"
    )

    metas.append({"tag": "link", "rel": "alternate", "type": "application/json+oembed", "href": oembed_url})

    metas += get_twitter_card_metas(type="user", id=user.id)

    return metas


def get_request_head_tags(request):
    view_info = get_view_info(request.path)
    if not view_info:
        return []
    view_name, view_arguments = view_info
    print(view_name, view_arguments)

    if view_name == "bp_spa.user_track":
        return get_user_track_tags(view_name, view_arguments)
    elif view_name == "bp_spa.user_album":
        return get_user_album_tags(view_name, view_arguments)
    elif view_name == "bp_spa.user_profile":
        return get_user_profile_tags(view_name, view_arguments)
    return []
