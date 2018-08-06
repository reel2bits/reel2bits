from flask import Blueprint, request, abort, current_app, Response, jsonify
from flask_accept import accept
from little_boxes import activitypub
from little_boxes.httpsig import verify_request

bp_ap = Blueprint('bp_ap', __name__)


@bp_ap.route('/user/<string:name>/inbox', methods=["GET", "POST"])
@accept('application/json',
        'application/activity+json',
        'application/jrd+json')
def user_inbox(name):
    be = activitypub.get_backend()
    if not be:
        abort(500)
    data = request.get_json(force=True)
    if not data:
        abort(500)
    current_app.logger.debug(f"req_headers={request.headers}")
    current_app.logger.debug(f"raw_data={data}")


@bp_ap.route('/user/<string:name>/outbox', methods=["GET", "POST"])
@accept('application/json',
        'application/activity+json',
        'application/jrd+json')
def user_outbox(name):
    be = activitypub.get_backend()
    if not be:
        abort(500)
    data = request.get_json(force=True)
    if not data:
        abort(500)
    current_app.logger.debug(f"req_headers={request.headers}")
    current_app.logger.debug(f"raw_data={data}")


@bp_ap.route('/inbox', methods=["GET", "POST"])
@accept('application/json',
        'application/activity+json',
        'application/jrd+json')
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

    # TODO save activity

    return Response(status=201)
