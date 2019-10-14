from flask import Blueprint, request, jsonify, abort, render_template
from models import db, OAuth2Client, User
from werkzeug.security import gen_salt
from app_oauth import authorization
from werkzeug.datastructures import ImmutableMultiDict

bp_api_v1_auth = Blueprint("bp_api_v1_auth", __name__)


@bp_api_v1_auth.route("/api/v1/apps", methods=["POST"])
def create_client():
    """
    Create a new application to obtain OAuth2 credentials.
    ---
    tags:
        - Apps
    responses:
        200:
            description: Returns App with client_id and client_secret
    """
    if request.form:
        req = request.form
    elif request.json:
        req = request.json
    else:
        abort(400)

    err = False
    if "client_name" not in req:
        err = True
    elif "redirect_uris" not in req:
        err = True
    elif "scopes" not in req:
        err = True

    if err:
        resp = {"error": "Required fields: client_name, redirect_uris, scopes"}
        response = jsonify(resp)
        response.mimetype = "application/json; charset=utf-8"
        response.status_code = 400
        return response

    client = OAuth2Client()
    client.client_name = req.get("client_name")
    client.client_uri = req.get("website", None)
    client.redirect_uri = req.get("redirect_uris")
    client.scope = req.get("scopes")
    client.client_id = gen_salt(24)
    if client.token_endpoint_auth_method == "none":
        client.client_secret = ""
    else:
        client.client_secret = gen_salt(48)
    # this needs to be hardcoded for whatever reason
    client.response_type = "code"
    client.grant_type = "authorization_code\r\nclient_credentials\r\npassword"
    client.token_endpoint_auth_method = "client_secret_post"

    db.session.add(client)
    db.session.commit()

    resp = {
        "client_id": client.client_id,
        "client_secret": client.client_secret,
        "id": client.id,
        "name": client.client_name,
        "redirect_uri": client.redirect_uri,
        "website": client.client_uri,
        "vapid_key": None,  # FIXME to implement this
    }
    response = jsonify(resp)
    response.mimetype = "application/json; charset=utf-8"
    response.status_code = 200
    return response


# This endpoint is used by the grants: authorization_code and implicit
@bp_api_v1_auth.route("/oauth/authorize", methods=["GET", "POST"])
def oauth_authorize():
    """
    Redirect here with response_type=code, client_id, client_secret, redirect_uri, scope.
    Displays an authorization form to the user.
    If approved, it will create and return an authorization code, then redirect to the desired redirect_uri, or show the authorization code if urn:ietf:wg:oauth:2.0:oob was requested.
    ---
    tags:
        - Authentication
    responses:
        200:
            description: ???
    """
    # input: client_id, client_secret, redirect_uri, scope
    # should authorize the user, and then return auth code if urn:ietf:wg:oauth:2.0:oob or redirect
    if request.method == "GET":
        scopes = request.args.get("scope", "").split(" ")
        return render_template("oauth/authorize.jinja2", scopes=scopes)
    else:
        grant_user = None

        if "username" and "password" in request.form:
            username = request.form.get("username")
            user = User.query.filter_by(name=username).first()
            if user and user.check_password(request.form.get("password")):
                grant_user = user

        return authorization.create_authorization_response(grant_user=grant_user)


@bp_api_v1_auth.route("/oauth/token", methods=["POST"])
def oauth_token():
    """
    Post here with authorization_code for authorization code grant type or username and password for password grant type.
    Returns an access token.
    This corresponds to the token endpoint, section 3.2 of the OAuth 2 RFC.
    ---
    tags:
        - Authentication
    responses:
        200:
            description: ???
    """
    if request.json:
        # Ugly workaround because authlib doesn't handle JSON queries
        d = {
            "client_id": request.json["client_id"],
            "client_secret": request.json["client_secret"],
            "grant_type": request.json["grant_type"],
            # This is an admin-fe workaround because scopes aren't specified
            "scope": request.json.get("scope", "read write follow"),
        }
        if request.json.get("password"):
            d["password"] = request.json["password"]
        if request.json.get("username"):
            d["username"] = request.json["username"]
        if request.json.get("code"):
            d["code"] = request.json["code"]
        if request.json.get("redirect_uri"):
            d["redirect_uri"] = request.json["redirect_uri"]

        request.form = ImmutableMultiDict(d)
    return authorization.create_token_response()


@bp_api_v1_auth.route("/oauth/revoke", methods=["POST"])
def oauth_revoke():
    """
    Post here with client credentials (in basic auth or in params client_id and client_secret) to revoke an access token.
    This corresponds to the token endpoint, using the OAuth 2.0 Token Revocation RFC (RFC 7009).
    ---
    tags:
        - Authentication
    responses:
        200:
            description: ???
    """
    # This endpoint wants basic auth, and it doesn't even works
    return authorization.create_endpoint_response("revocation")
