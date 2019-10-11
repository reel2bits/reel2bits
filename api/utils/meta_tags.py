from flask import current_app, url_for
from models import Config, User, Sound, Album
from utils.various import join_url
from werkzeug.routing import RequestRedirect, MethodNotAllowed, NotFound


def get_view_info(url, method="GET"):
    """Match a url and return the view and arguments
    it will be called with, or None if there is no view.
    """

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
    # Uses type and ID
    embed_url = None
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

    track_url = url_for(
        "bp_spa.user_track", username=view_arguments["username"], trackslug=view_arguments["trackslug"], _external=True
    )
    musician_url = url_for("bp_spa.user_profile", username=view_arguments["username"], _external=True)
    transcode_url = url_for("get_uploads_stuff", thing="sounds", stuff=track.path_sound(orig=False), _external=True)

    metas = [
        {"tag": "meta", "property": "og:url", "content": track_url},
        {"tag": "meta", "property": "og:title", "content": track.title},
        {"tag": "meta", "property": "og:type", "content": "music.song"},
        {"tag": "meta", "property": "music:musician", "content": musician_url},
    ]

    if track.album:
        album_url = url_for(
            "bp_spa.user_album", username=view_arguments["username"], albumslug=track.album.slug, _external=True
        )
        metas.append({"tag": "meta", "property": "music:album:disc", "content": 1})
        metas.append({"tag": "meta", "property": "music:album:track", "content": track.album_order})
        metas.append({"tag": "meta", "property": "music:album", "content": album_url})
    if track.artwork_filename:
        url_artwork = url_for("get_uploads_stuff", thing="artwork_sounds", stuff=track.path_artwork(), _external=True)
    else:
        url_artwork = join_url(current_app.config["REEL2BITS_URL"], "/static/artwork_placeholder.png")
    metas.append({"tag": "meta", "property": "og:image", "content": url_artwork})
    metas.append({"tag": "meta", "property": "og:audio", "content": transcode_url})
    # TODO link for oembed
    # TODO twitter card thing
    # metas += get_twitter_card_metas(type='track', id=track.id)
    return metas


def get_user_album_tags(view_name, view_arguments):
    user = get_user(view_arguments)
    if not user:
        return []

    album = Album.query.filter(Album.user_id == user.id, Album.private.is_(False)).first()
    if not album:
        return []

    album_url = url_for(
        "bp_spa.user_album", username=view_arguments["username"], albumslug=view_arguments["albumslug"], _external=True
    )
    musician_url = url_for("bp_spa.user_profile", username=view_arguments["username"], _external=True)
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

    # TODO link for oembed
    # TODO twitter card thing
    # metas += get_twitter_card_metas(type='album', id=album.id)

    return metas


def get_user_profile_tags(view_name, view_arguments):
    user = get_user(view_arguments)
    if not user:
        return []

    feed_url = url_for("bp_feeds.tracks", user_id=user.id, _external=True)
    musician_url = url_for("bp_spa.user_profile", username=view_arguments["username"], _external=True)

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

    # TODO link for oembed
    # TODO twitter card thing
    # metas += get_twitter_card_metas(type='artist', id=user.id)

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
