from flask import Blueprint, jsonify, request, current_app, url_for
from utils.meta_tags import get_view_info
from utils.various import join_url
from models import Sound, User, Config, Album
import urllib.parse

bp_api_oembed = Blueprint("bp_api_oembed", __name__)


@bp_api_oembed.route("/api/oembed", methods=["GET"])
def provider():
    """
    OEmbed provider.
    ---
    tags:
        - OEmbed
    responses:
        200:
            description: Returns the OEmbed thing
    """
    format = request.args.get("format", "json")
    url = request.args.get("url", None)
    if not url:
        # yep it's awful, should get fixed in app.py:page_not_found()/app.py:render_tags() I guess
        url = request.args.get("amp;url", None)
        if not url:
            return jsonify("no url given"), 400
    if format not in ["json"]:
        return jsonify("unsupported format"), 400

    _config = Config.query.first()
    if not _config:
        return jsonify("application error: no config"), 500

    url = urllib.parse.urlparse(url)

    view_info = get_view_info(url.path)
    if not view_info:
        return jsonify([]), 400

    view_name, view_arguments = view_info

    data = {
        "version": "1.0",
        "type": "rich",
        "provider_name": _config.app_name,
        "provider_url": current_app.config["REEL2BITS_URL"],
        "height": 400,
        "width": 600,
    }

    embed_id = None
    embed_type = None

    def get_user():
        return User.query.filter(User.name == view_arguments["username"], User.local.is_(True)).first()

    if view_name == "bp_spa.user_track":
        user = get_user()
        if not user:
            return jsonify("user not found"), 404
        track = Sound.query.filter(
            Sound.slug == view_arguments["trackslug"],
            Sound.user_id == user.id,
            Sound.private.is_(False),
            Sound.transcode_state == Sound.TRANSCODE_DONE,
        ).first()
        if not track:
            return jsonify("track not found"), 404

        embed_id = track.id
        embed_type = "track"

        data["title"] = f"{track.title} by {track.user.name}"
        if track.artwork_filename:
            url_artwork = url_for(
                "get_uploads_stuff", thing="artwork_sounds", stuff=track.path_artwork(), _external=True
            )
        else:
            url_artwork = join_url(current_app.config["REEL2BITS_URL"], "/static/artwork_placeholder.png")
        data["thumbnail_url"] = url_artwork
        data["thumbnail_width"] = 112
        data["thumbnail_height"] = 112
        data["description"] = track.description
        data["author_name"] = track.user.name
        data["height"] = 150
        data["author_url"] = url_for("bp_spa.user_profile", username=user.name, _external=True)
    elif view_name == "bp_spa.user_album":
        user = get_user()
        if not user:
            return jsonify("user not found"), 404
        album = Album.query.filter(
            Album.slug == view_arguments["albumslug"], Album.private.is_(False), Album.user_id == user.id
        ).first()
        if not album:
            return jsonify("album not found"), 404

        embed_id = album.id
        embed_type = "album"

        if album.artwork_filename:
            url_artwork = url_for(
                "get_uploads_stuff", thing="artwork_albums", stuff=album.path_artwork(), _external=True
            )
        else:
            url_artwork = join_url(current_app.config["REEL2BITS_URL"], "/static/artwork_placeholder.png")

        data["thumbnail_url"] = url_artwork
        data["thumbnail_width"] = 112
        data["thumbnail_height"] = 112
        data["title"] = f"{album.title} by {album.user.name}"
        data["description"] = album.description
        data["author_name"] = album.user.name
        data["height"] = 400
        data["author_url"] = url_for("bp_spa.user_profile", username=user.name, _external=True)
    elif view_name == "bp_spa.user_profile":
        user = get_user()
        if not user:
            return jsonify("user not found"), 404

        embed_id = user.id
        embed_type = "user"

        if user.avatar_filename:
            url_avatar = url_for("get_uploads_stuff", thing="avatars", stuff=user.path_avatar(), _external=True)
        else:
            url_avatar = join_url(current_app.config["REEL2BITS_URL"], "/static/userpic_placeholder.png")
        data["thumbnail_url"] = url_avatar
        data["thumbnail_width"] = 112
        data["thumbnail_height"] = 112
        data["title"] = user.name
        data["description"] = user.actor[0].summary
        data["author_name"] = user.name
        data["height"] = 400
        data["author_url"] = url_for("bp_spa.user_profile", username=user.name, _external=True)
    else:
        return jsonify("page not found"), 404

    embed_url = url_for("bp_api_embed.iframe", kind=embed_type, id=embed_id, _external=True)
    data[
        "html"
    ] = f'<iframe width="{data["width"]}" height="{data["height"]}" scrolling="no" frameborder="no" src="{embed_url}"></iframe>'

    return jsonify(data)
