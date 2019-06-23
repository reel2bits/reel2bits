from flask import Blueprint, request, jsonify, abort
from models import db, OAuth2Client, User
from werkzeug.security import gen_salt
from app_oauth import authorization

bp_api_v1_auth = Blueprint("bp_api_v1_auth", __name__)


@bp_api_v1_auth.route("/api/v1/apps", methods=["POST"])
def create_client():
    """
    Eats: client_name, redirect_uris, scopes, website(opt)
    :return:
    """
    err = False
    if not 'client_name' in request.form:
        err = True
    elif not 'redirect_uris' in request.form:
        err = True
    elif not 'scopes' in request.form:
        err = True

    if err:
        resp = {"error": "Required fields: client_name, redirect_uris, scopes"}
        response = jsonify(resp)
        response.mimetype = "application/json; charset=utf-8"
        response.status_code = 400
        return response

    client = OAuth2Client()
    client.client_name = request.form.get('client_name')
    client.client_uri = request.form.get('website', None)
    client.redirect_uri = request.form.get('redirect_uris')
    client.scope = request.form.get('scopes')
    client.client_id = gen_salt(24)
    if client.token_endpoint_auth_method == 'none':
        client.client_secret = ''
    else:
        client.client_secret = gen_salt(48)
    # this needs to be hardcoded for whatever reason
    client.response_type = 'code'
    client.grant_type = 'authorization_code\r\nclient_credentials\r\npassword'
    client.token_endpoint_auth_method = 'client_secret_post'

    db.session.add(client)
    db.session.commit()

    resp = {
        "client_id": client.client_id,
        "client_secret": client.client_secret,
        "id": client.id,
        "name": client.client_name,
        "redirect_uri": client.redirect_uri,
        "website": client.client_uri,
        "vapid_key": None  # FIXME to implement this
    }
    response = jsonify(resp)
    response.mimetype = "application/json; charset=utf-8"
    response.status_code = 200
    return response


# This endpoint is used by the grants: authorization_code and implicit
@bp_api_v1_auth.route("/oauth/authorize", methods=["GET", "POST"])
def oauth_authorize():
    # input: client_id, client_secret, redirect_uri, scope
    # should authorize the user, and then return auth code if urn:ietf:wg:oauth:2.0:oob or redirect
    if request.method == 'GET':
        abort(404)
    else:
        grant_user = None

        if 'username' and 'password' in request.form:
            username = request.form.get('username')
            user = User.query.filter_by(name=username).first()
            if user and user.check_password(request.form.get('password')):
                grant_user = user

        return authorization.create_authorization_response(grant_user=grant_user)


@bp_api_v1_auth.route("/oauth/token", methods=["POST"])
def oauth_token():
    return authorization.create_token_response()


@bp_api_v1_auth.route("/oauth/revoke", methods=["POST"])
def oauth_revoke():
    # input: client_id, client_secret
    return authorization.create_endpoint_response('revocation')
