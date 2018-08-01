from flask import Blueprint, current_app, request, jsonify, Response

from models import db, Config, User, Sound

bp_nodeinfo = Blueprint('bp_nodeinfo', __name__, url_prefix='/nodeinfo')


@bp_nodeinfo.route('/2.0', methods=['GET'])
def nodeinfo():
    _config = Config.query.one()
    if not _config:
        return Response("", status=500)

    resp = {
        "version": "2.0",
        "software": {
            "name": "reel2bits",
            "version": None
        },
        "services": {
            "inbound": [],
            "outbound": []
        },
        "protocols": [
            "activitypub"
        ],
        "openRegistrations": current_app.config['SECURITY_REGISTERABLE'],
        "usage": {
            "localPosts": db.session.query(Sound.id).count(), # FIXME
            "users": {
                "total": db.session.query(User.id).count() # FIXME
            }
        },
        "metadata": {
            "nodeName": _config.app_name,
            "nodeDescription": _config.app_description,
            "taxonomy": {
                "postsName": "Tracks"
            }
        }
    }


    response = jsonify(resp)
    response.mimetype = 'application/json; charset=utf-8; profile="http://nodeinfo.diaspora.software/ns/schema/2.0#"'
    return response
