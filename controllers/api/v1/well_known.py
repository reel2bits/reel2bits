from flask import Blueprint, current_app, request, jsonify, Response

bp_wellknown = Blueprint('bp_wellknown', __name__, url_prefix='/.well-known')


@bp_wellknown.route('/webfinger', methods=['GET'])
def webfinger():
    resource = request.args.get('resource')
    if not resource:
        return Response("", status=400)

    id_list = resource.split(":")
    if len(id_list) < 2:
        return Response("", status=400)

    try:
        user_id, domain = id_list[1].split("@")
    except ValueError:
        return Response("", status=400)

    if len(id_list) == 3:
        domain += f":{id_list[2]}"

    if not (domain == current_app.config['AP_DOMAIN']):
        return Response("", status=404)

    method = "https"

    resp = {
        "subject": f"acct:{user_id}@{domain}",
        "aliases": [
            f"{method}://{domain}/user/{user_id}"
        ],
        "links": [
            {
                "rel": "self",
                "type": "application/activity+json",
                "href": f"{method}://{domain}/user/{user_id}"
            },
        ]
    }

    response = jsonify(resp)
    response.mimetype = "application/jrd+json; charset=utf-8"
    return response


@bp_wellknown.route('/nodeinfo', methods=['GET'])
def nodeinfo():
    method = "https"
    domain = current_app.config['AP_DOMAIN']
    resp = {
        "links": [
            {
                "rel": "http://nodeinfo.diaspora.software/ns/schema/2.0",
                "href": f"{method}://{domain}/nodeinfo/2.0"
            }
        ]
    }
    response = jsonify(resp)
    response.mimetype = 'application/json; charset=utf-8'
    return response
