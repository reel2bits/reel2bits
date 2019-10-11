from flask import Blueprint, abort

bp_api_embed = Blueprint("bp_api_embed", __name__)


@bp_api_embed.route("/api/embed/<string:kind>/<int:id>", methods=["GET"])
def iframe(kind, id):
    """
    Embedded iFrame provider.
    ---
    tags:
        - Embed
    responses:
        200:
            description: Returns the iframe thing
    """
    if kind not in ["user", "track", "album"]:
        abort(400)

    return ""
