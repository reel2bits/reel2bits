from flask import Blueprint, current_app, jsonify, Response, g, abort
from utils.various import RESTRICTED_NICKNAMES
from models import db, Config, User, Sound

bp_nodeinfo = Blueprint("bp_nodeinfo", __name__, url_prefix="/nodeinfo")


@bp_nodeinfo.route("/<string:version>", methods=["GET"])
def nodeinfo(version):
    """
    Nodeinfo endpoint
    ---
    tags:
        - Nodeinfo
    parameters:
        - name: version
          in: path
          type: string
          enum: ['2.0', '2.1']
          required: true
          default: '2.1'
          description: Nodeinfo version
    responses:
        200:
            description: Nodeinfo
    """
    _config = Config.query.one()
    if not _config:
        return Response("", status=500, content_type="application/jrd+json; charset=utf-8")

    if version not in ["2.0", "2.1"]:
        abort(404)

    resp = {
        "version": version,
        "software": {"name": "reel2bits", "version": g.cfg["REEL2BITS_VERSION"]},
        "services": {"inbound": [], "outbound": []},
        "protocols": [],
        "openRegistrations": current_app.config["REGISTRATION_ENABLED"],
        "usage": {
            "localPosts": db.session.query(Sound.id).count(),
            "users": {"total": db.session.query(User.id).count()},
        },
        "metadata": {
            "nodeName": _config.app_name,
            "nodeDescription": _config.app_description,
            "taxonomy": {"postsName": "Tracks"},
            "restrictedNicknames": RESTRICTED_NICKNAMES,
            "uploadLimits": {"track": current_app.config["UPLOAD_TRACK_MAX_SIZE"]},
        },
    }

    if current_app.config["SENTRY_DSN"]:
        resp["metadata"]["sentryDsn"] = current_app.config["SENTRY_DSN"]
    else:
        resp["metadata"]["sentryDsn"] = None

    resp["metadata"]["announcement"] = _config.announcement

    if current_app.config["AP_ENABLED"]:
        resp["protocols"].append("activitypub")

    if version == "2.1":
        resp["software"]["repository"] = current_app.config["SOURCES_REPOSITORY_URL"]

    response = jsonify(resp)
    response.mimetype = (
        "application/json; charset=utf-8; profile=" f'"http://nodeinfo.diaspora.software/ns/schema/{version}#"'
    )
    return response
