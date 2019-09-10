from flask import Blueprint, request, abort, current_app, Response, jsonify, flash, render_template, redirect, url_for
from little_boxes import activitypub
from little_boxes.httpsig import verify_request
from activitypub.vars import Box
from tasks import post_to_inbox
from activitypub.utils import activity_from_doc, build_ordered_collection
from models import Activity, User
from flask_accept import accept_fallback
from flask_babelex import gettext

bp_ap = Blueprint("bp_ap", __name__)


@bp_ap.route("/user/<string:name>", methods=["GET"])
def user_actor_json(name):
    user = User.query.filter(User.name == name).first()
    if not user:
        return Response("", status=404)
    actors = user.actor
    if len(actors) <= 0:
        return Response("", status=500)

    response = jsonify(actors[0].to_dict())
    response.mimetype = "application/activity+json; charset=utf-8"
    return response


@bp_ap.route("/user/<string:name>/inbox", methods=["GET", "POST"])
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
    be = activitypub.get_backend()
    if not be:
        abort(500)
    data = request.get_json(force=True)
    if not data:
        abort(500)
    current_app.logger.debug(f"req_headers={request.headers}")
    current_app.logger.debug(f"raw_data={data}")


@bp_ap.route("/user/<string:name>/followings", methods=["GET"])
@accept_fallback
def followings(name):
    pcfg = {"title": gettext("%(username)s' followings", username=name)}

    user = User.query.filter(User.name == name).first()
    if not user:
        flash(gettext("User not found"), "error")
        return redirect(url_for("bp_main.home"))

    followings_list = user.actor[0].followings

    return render_template(
        "users/followings.jinja2", pcfg=pcfg, user=user, actor=user.actor[0], followings=followings_list
    )


@bp_ap.route("/user/<string:name>/followings", methods=["GET", "POST"])
@followings.support("application/json", "application/activity+json")
def user_followings(name):
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


@bp_ap.route("/user/<string:name>/followers", methods=["GET"])
@accept_fallback
def followers(name):
    pcfg = {"title": gettext("%(username)s' followers", username=name)}

    user = User.query.filter(User.name == name).first()
    if not user:
        flash(gettext("User not found"), "error")
        return redirect(url_for("bp_main.home"))

    followers_list = user.actor[0].followers

    return render_template(
        "users/followers.jinja2", pcfg=pcfg, user=user, actor=user.actor[0], followers=followers_list
    )


@bp_ap.route("/user/<string:name>/followers", methods=["GET", "POST"])
@followers.support("application/json", "application/activity+json")
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
    followers_list = actor.followers

    return jsonify(**build_ordered_collection(followers_list, actor.url, request.args.get("page")))


@bp_ap.route("/inbox", methods=["GET", "POST"])
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


@bp_ap.route("/outbox", methods=["GET", "POST"])
def outbox():
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
