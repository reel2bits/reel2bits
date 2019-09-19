from flask import Blueprint, current_app, request, jsonify, Response
from models import db, User, Actor

bp_wellknown = Blueprint("bp_wellknown", __name__, url_prefix="/.well-known")


@bp_wellknown.route("/webfinger", methods=["GET"])
def webfinger():
    """
    ???
    ---
    tags:
        - ActivityPub
    parameters:
        - name: resource
          in: query
          type: string
          required: true
          description: user@host
    responses:
        200:
            description: ???
    """
    resource = request.args.get("resource")
    if not resource:
        return Response("", status=400, content_type="application/jrd+json; charset=utf-8")

    if resource.startswith("https://"):
        actor = db.session.query(Actor).filter_by(url=resource).first()
        user = actor.user
        domain = actor.domain
    else:
        id_list = resource.split(":")
        if len(id_list) < 2:
            return Response("", status=400, content_type="application/jrd+json; charset=utf-8")

        try:
            user_id, domain = id_list[1].split("@")
        except ValueError:
            return Response("", status=400, content_type="application/jrd+json; charset=utf-8")

        if len(id_list) == 3:
            domain += f":{id_list[2]}"

        if not (domain == current_app.config["AP_DOMAIN"]):
            return Response("", status=404, content_type="application/jrd+json; charset=utf-8")

        user = db.session.query(User).filter_by(name_insensitive=user_id).first()
        if not user:
            return Response("", status=404, content_type="application/jrd+json; charset=utf-8")

    method = "https"

    resp = {
        "subject": f"acct:{user.name}@{domain}",
        "aliases": [f"{method}://{domain}/user/{user.name}"],
        "links": [
            {"rel": "self", "type": "application/activity+json", "href": f"{method}://{domain}/user/{user.name}"}
        ],
    }

    response = jsonify(resp)
    response.mimetype = "application/jrd+json; charset=utf-8"
    return response


@bp_wellknown.route("/nodeinfo", methods=["GET"])
def nodeinfo():
    """
    ???
    ---
    tags:
        - Nodeinfo
    responses:
        200:
            description: ???
    """
    method = "https"
    domain = current_app.config["AP_DOMAIN"]
    resp = {
        "links": [
            {"rel": "http://nodeinfo.diaspora.software/ns/schema/2.0", "href": f"{method}://{domain}/nodeinfo/2.0"},
            {"rel": "http://nodeinfo.diaspora.software/ns/schema/2.1", "href": f"{method}://{domain}/nodeinfo/2.1"},
        ]
    }
    response = jsonify(resp)
    response.mimetype = "application/json; charset=utf-8"
    return response
