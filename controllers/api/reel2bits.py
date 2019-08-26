from flask import Blueprint, jsonify
from models import licences

bp_api_reel2bits = Blueprint("bp_api_reel2bits", __name__)


@bp_api_reel2bits.route("/api/reel2bits/licenses", methods=["GET"])
def licenses():
    """
    List of various licenses.
    ---
    tags:
        - Tracks
    responses:
        200:
            description: Returns a list of various licenses.
    """
    resp = [licences[i] for i in licences]
    response = jsonify(resp)
    response.mimetype = "application/json; charset=utf-8"
    response.status_code = 200
    return response
