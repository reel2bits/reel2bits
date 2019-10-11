from flask import Blueprint, abort

bp_spa = Blueprint("bp_spa", __name__)


@bp_spa.route("/<string:username>/track/<string:trackslug>", methods=["GET"])
def user_track(username, trackslug):
    abort(404)


@bp_spa.route("/<string:username>/album/<string:albumslug>", methods=["GET"])
def user_album(username, albumslug):
    abort(404)


@bp_spa.route("/<string:username>", methods=["GET"])
def user_profile(username):
    abort(404)
