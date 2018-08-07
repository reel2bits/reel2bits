from flask import Blueprint, request, abort, current_app, Response, jsonify
from little_boxes import activitypub
from little_boxes.httpsig import verify_request
from activitypub.backend import post_to_inbox, Box
from activitypub.utils import activity_from_doc, build_ordered_collection
from models import Activity, User


bp_ap = Blueprint('bp_ap', __name__)


@bp_ap.route('/user/<string:name>/inbox', methods=["GET", "POST"])
def user_inbox(name):
    be = activitypub.get_backend()
    if not be:
        abort(500)
    data = request.get_json(force=True)
    if not data:
        abort(500)

    current_app.logger.debug(f"req_headers={request.headers}")
    current_app.logger.debug(f"raw_data={data}")

    try:
        if not verify_request(request.method,
                              request.path,
                              request.headers,
                              request.data):
            raise Exception("failed to verify request")
    except Exception:
        current_app.logger.exception("failed to verify request")
        try:
            data = be.fetch_iri(data["id"])
        except Exception:
            current_app.logger.exception(f"failed to fetch remote id "
                                         f"at {data['id']}")
            resp = {
                "error": "failed to verify request "
                         "(using HTTP signatures or fetching the IRI)"
            }
            response = jsonify(resp)
            response.mimetype = "application/json; charset=utf-8"
            response.status = 422
            return response

    activity = activitypub.parse_activity(data)
    current_app.logger.debug(f"inbox_activity={activity}/{data}")

    post_to_inbox(activity)

    return Response(status=201)


@bp_ap.route('/user/<string:name>/outbox', methods=["GET", "POST"])
def user_outbox(name):
    be = activitypub.get_backend()
    if not be:
        abort(500)
    data = request.get_json(force=True)
    if not data:
        abort(500)
    current_app.logger.debug(f"req_headers={request.headers}")
    current_app.logger.debug(f"raw_data={data}")


@bp_ap.route('/user/<string:name>/followers', methods=["GET", "POST"])
def user_followers(name):
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
    followers = actor.followers

    return jsonify(
        **build_ordered_collection(
            followers,
            actor.url,
            request.args.get("page")
        )
    )


@bp_ap.route('/inbox', methods=["GET", "POST"])
def inbox():
    be = activitypub.get_backend()
    if not be:
        abort(500)
    data = request.get_json(force=True)
    if not data:
        abort(500)

    current_app.logger.debug(f"req_headers={request.headers}")
    current_app.logger.debug(f"raw_data={data}")

    try:
        if not verify_request(request.method,
                              request.path,
                              request.headers,
                              request.data):
            raise Exception("failed to verify request")
    except Exception:
        current_app.logger.exception("failed to verify request")
        try:
            data = be.fetch_iri(data["id"])
        except Exception:
            current_app.logger.exception(f"failed to fetch remote id "
                                         f"at {data['id']}")
            resp = {
                "error": "failed to verify request "
                         "(using HTTP signatures or fetching the IRI)"
            }
            response = jsonify(resp)
            response.mimetype = "application/json; charset=utf-8"
            response.status = 422
            return response

    activity = activitypub.parse_activity(data)
    current_app.logger.debug(f"inbox_activity={activity}/{data}")

    post_to_inbox(activity)

    return Response(status=201)


@bp_ap.route('/outbox', methods=["GET", "POST"])
def outbox():
    be = activitypub.get_backend()
    if not be:
        abort(500)
    data = request.get_json(force=True)
    if not data:
        abort(500)
    current_app.logger.debug(f"req_headers={request.headers}")
    current_app.logger.debug(f"raw_data={data}")


@bp_ap.route('/outbox/<string:item_id>', methods=["GET", "POST"])
def outbox_item(item_id):
    be = activitypub.get_backend()
    if not be:
        abort(500)
    # data = request.get_json()
    # if not data:
    #     abort(500)
    current_app.logger.debug(f"req_headers={request.headers}")
    # current_app.logger.debug(f"raw_data={data}")

    current_app.logger.debug(f"activity url {be.activity_url(item_id)}")

    item = Activity.query.filter(Activity.box == Box.OUTBOX.value,
                                 Activity.url == be.activity_url(item_id)
                                 ).first()
    if not item:
        abort(404)

    # check if deleted, if yes, return 410 tombstone gone

    current_app.logger.debug(f"item payload=={item.payload}")

    return jsonify(**activity_from_doc(item.payload))
