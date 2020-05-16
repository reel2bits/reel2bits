from flask import Blueprint, request, abort, current_app, Response, jsonify, g
from little_boxes import activitypub
from little_boxes.httpsig import verify_request
from activitypub.vars import Box
from tasks import post_to_inbox
from activitypub.utils import activity_from_doc, build_ordered_collection
from models import db, Activity, User, Actor, Role, Config, Sound

bp_ap = Blueprint("bp_ap", __name__)


@bp_ap.route("/user/<string:name>", methods=["GET"])
def user_actor_json(name):
    """
    Actor
    ---
    tags:
        - ActivityPub
    responses:
        200:
            description: Returns an actor
        404:
            description: The actor cannot be found
        410:
            description: The actor have been deleted
    """
    actor = Actor.query.filter(
        Actor.preferred_username == name, Actor.domain == current_app.config["AP_DOMAIN"]
    ).first()
    if not actor:
        return Response("", status=404, mimetype="application/activity+json; charset=utf-8")

    if not actor.meta_deleted:
        response = jsonify(actor.to_dict())
    else:
        # Get the tombstone
        # tomb = Activity.query.filter(
        #     Activity.type == "Delete",
        #     Activity.box == "outbox",
        #     Activity.local.is_(True),
        #     Activity.actor_id == actor.id,
        #     Activity.payload[("object", "type")].astext == "Tombstone",
        #     Activity.payload[("object", "id")].astext == actor.url,
        # ).one()
        return Response(response="", status=410, mimetype="application/activity+json; charset=utf-8")

    response.mimetype = "application/activity+json; charset=utf-8"
    return response


@bp_ap.route("/user/<string:name>/inbox", methods=["GET", "POST"])
def user_inbox(name):
    """
    User inbox
    ---
    tags:
        - ActivityPub
    responses:
        200:
            description: Returns something
    """
    be = activitypub.get_backend()
    if not be:
        abort(500)
    data = request.get_json(force=True)
    if not data:
        abort(500)

    current_app.logger.debug(f"req_headers={request.headers}")
    current_app.logger.debug(f"raw_data={data}")

    try:
        if not verify_request(request.method, request.path, request.headers, request.data):
            raise Exception("failed to verify request")
    except Exception:
        current_app.logger.exception("failed to verify request")
        try:
            data = be.fetch_iri(data["id"])
        except Exception:
            current_app.logger.exception(f"failed to fetch remote id " f"at {data['id']}")
            resp = {"error": "failed to verify request " "(using HTTP signatures or fetching the IRI)"}
            response = jsonify(resp)
            response.mimetype = "application/json; charset=utf-8"
            response.status = 422
            return response

    activity = activitypub.parse_activity(data)
    current_app.logger.debug(f"inbox_activity={activity}/{data}")

    post_to_inbox(activity)

    return Response(status=201)


@bp_ap.route("/user/<string:name>/outbox", methods=["GET", "POST"])
def user_outbox(name):
    """
    User outbox
    ---
    tags:
        - ActivityPub
    responses:
        200:
            description: Returns something
    """
    be = activitypub.get_backend()
    if not be:
        abort(500)
    data = request.get_json(force=True)
    if not data:
        abort(500)
    current_app.logger.debug(f"req_headers={request.headers}")
    current_app.logger.debug(f"raw_data={data}")


@bp_ap.route("/user/<string:name>/followings", methods=["GET", "POST"])
def user_followings(name):
    """
    User followings
    ---
    tags:
        - ActivityPub
    responses:
        200:
            description: Returns a collection of Actors
    """
    be = activitypub.get_backend()
    if not be:
        abort(500)
    # data = request.get_json(force=True)
    # if not data:
    #     abort(500)
    current_app.logger.debug(f"req_headers={request.headers}")
    # current_app.logger.debug(f"raw_data={data}")

    user = User.query.filter(User.name == name).first()
    if not user:
        abort(404)

    actor = user.actor[0]
    followings_list = actor.followings

    return jsonify(**build_ordered_collection(followings_list, actor.url, request.args.get("page"), switch_side=True))


@bp_ap.route("/user/<string:name>/followers", methods=["GET", "POST"])
def user_followers(name):
    """
    User followers
    ---
    tags:
        - ActivityPub
    responses:
        200:
            description: Returns a collection of Actors
    """
    be = activitypub.get_backend()
    if not be:
        abort(500)
    # data = request.get_json(force=True)
    # if not data:
    #     abort(500)
    current_app.logger.debug(f"req_headers={request.headers}")
    # current_app.logger.debug(f"raw_data={data}")

    user = User.query.filter(User.name == name).first()
    if not user:
        abort(404)

    actor = user.actor[0]
    followers_list = actor.followers

    return jsonify(**build_ordered_collection(followers_list, actor.url, request.args.get("page")))


@bp_ap.route("/inbox", methods=["GET", "POST"])
def inbox():
    """
    Global inbox
    ---
    tags:
        - ActivityPub
    responses:
        200:
            description: Returns something
    """
    be = activitypub.get_backend()
    if not be:
        abort(500)
    data = request.get_json(force=True)
    if not data:
        abort(500)

    current_app.logger.debug(f"req_headers={request.headers}")
    current_app.logger.debug(f"raw_data={data}")

    try:
        if not verify_request(request.method, request.path, request.headers, request.data):
            raise Exception("failed to verify request")
    except Exception:
        current_app.logger.exception("failed to verify request")
        try:
            data = be.fetch_iri(data["id"])
        except Exception:
            current_app.logger.exception(f"failed to fetch remote id " f"at {data['id']}")
            resp = {"error": "failed to verify request " "(using HTTP signatures or fetching the IRI)"}
            response = jsonify(resp)
            response.mimetype = "application/json; charset=utf-8"
            response.status = 422
            return response

    activity = activitypub.parse_activity(data)
    current_app.logger.debug(f"inbox_activity={activity!r}/{data!r}")

    post_to_inbox(activity)

    return Response(status=201)


@bp_ap.route("/outbox", methods=["GET", "POST"])
def outbox():
    """
    Global outbox
    ---
    tags:
        - ActivityPub
    responses:
        200:
            description: Returns something
    """
    be = activitypub.get_backend()
    if not be:
        abort(500)
    data = request.get_json(force=True)
    if not data:
        abort(500)
    current_app.logger.debug(f"req_headers={request.headers}")
    current_app.logger.debug(f"raw_data={data}")


@bp_ap.route("/outbox/<string:item_id>", methods=["GET", "POST"])
def outbox_item(item_id):
    """
    Outbox item
    ---
    tags:
        - ActivityPub
    responses:
        200:
            description: Returns something
    """
    be = activitypub.get_backend()
    if not be:
        abort(500)
    # data = request.get_json()
    # if not data:
    #     abort(500)
    current_app.logger.debug(f"req_headers={request.headers}")
    # current_app.logger.debug(f"raw_data={data}")

    current_app.logger.debug(f"activity url {be.activity_url(item_id)}")

    item = Activity.query.filter(Activity.box == Box.OUTBOX.value, Activity.url == be.activity_url(item_id)).first()
    if not item:
        abort(404)

    if item.meta_deleted:
        obj = activitypub.parse_activity(item.payload)
        resp = jsonify(**obj.get_tombstone().to_dict())
        resp.status_code = 410
        return resp

    current_app.logger.debug(f"item payload=={item.payload}")

    return jsonify(**activity_from_doc(item.payload))


@bp_ap.route("/outbox/<string:item_id>/activity", methods=["GET", "POST"])
def outbox_item_activity(item_id):
    """
    Outbox activity
    ---
    tags:
        - ActivityPub
    responses:
        200:
            description: Returns something
    """
    be = activitypub.get_backend()
    if not be:
        abort(500)

    item = Activity.query.filter(Activity.box == Box.OUTBOX.value, Activity.url == be.activity_url(item_id)).first()
    if not item:
        abort(404)

    obj = activity_from_doc(item.payload)

    if item.meta_deleted:
        obj = activitypub.parse_activity(item.payload)
        # FIXME not sure about that /activity
        tomb = obj.get_tombstone().to_dict()
        tomb["id"] = tomb["id"] + "/activity"
        resp = jsonify(tomb)
        resp.status_code = 410
        return resp

    if obj["type"] != activitypub.ActivityType.CREATE.value:
        abort(404)

    return jsonify(**obj["object"])


@bp_ap.route("/api/v1/instance/", methods=["GET"])
@bp_ap.route("/api/v1/instance", methods=["GET"])
def api_v1_instance():
    """
    Information about the server.
    ---
    tags:
        - ActivityPub
    definitions:
        URLs:
            type: object
            properties:
                streaming_api:
                    type: url
                    nullable: false
        Stats:
            type: object
            properties:
                user_count:
                    nullable: false
                    type: integer
                status_count:
                    nullable: false
                    type: integer
                domain_count:
                    nullable: false
                    type: integer
        Instance:
            type: object
            properties:
                uri:
                    type: string
                    nullable: false
                title:
                    type: string
                    nullable: false
                description:
                    type: string
                    nullable: false
                email:
                    type: string
                    nullable: false
                version:
                    type: string
                    nullable: false
                thumbnail:
                    type: url
                    nullable: true
                urls:
                    type: hash
                    nullable: false
                    items:
                        type: object
                        $ref: '#/definitions/URLs'
                stats:
                    type: hash
                    nullable: false
                    items:
                        type: object
                        $ref: '#/definitions/Stats'
                languages:
                    type: array
                    nullable: false
                    items:
                        type: string
                contact_account:
                    type: object
                    $ref: '#/definitions/Account'
                    nullable: true
    responses:
        200:
            description: Returns Instance
            schema:
                $ref: '#/definitions/Instance'
    """
    method = current_app.config["REEL2BITS_PROTOCOL"] or "https"
    domain = current_app.config["AP_DOMAIN"]
    _config = Config.query.one()
    if not _config:
        return Response("", status=500, content_type="application/jrd+json; charset=utf-8")
    user_count = db.session.query(User.id).filter(User.local.is_(True)).count()
    # TODO: when Sound.local is implemented (incoming sound), add a Sound.local.is_(True) to the filters
    status_count = (
        db.session.query(Sound.id)
        .filter(Sound.transcode_state == Sound.TRANSCODE_DONE, Sound.private.is_(False))
        .count()
    )
    domain_count = db.session.query(Actor.domain).filter(Actor.domain != domain).group_by(Actor.domain).count()
    first_admin_email = db.session.query(User.email).filter(User.roles.any(Role.name == "admin")).first()

    return jsonify(
        {
            "uri": f"{method}://{domain}",
            "title": _config.app_name,
            "description": _config.app_description,
            "email": first_admin_email[0] if first_admin_email else None,
            "version": g.cfg["REEL2BITS_VERSION"],
            "thumbnail": None,
            "urls": [],  # no 'streaming_api'
            "stats": {"domain_count": domain_count, "status_count": status_count, "user_count": user_count},
            "languages": ["en"],
            "contact_account": None,
        }
    )
