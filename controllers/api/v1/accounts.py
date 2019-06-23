from flask import Blueprint, request, jsonify, abort
from models import db, User, user_datastore, Role, create_actor, OAuth2Token
from flask_security.utils import encrypt_password
from flask_security import confirmable as FSConfirmable
from oauth import authorization
import datetime

bp_api_v1_accounts = Blueprint("bp_api_v1_accounts", __name__)


# Parameters needed:
#  nickname(==username), email, fullname, password, confirm, agreement, locale(dropped here for now)
# Optionals:
#  bio
@bp_api_v1_accounts.route("/api/v1/accounts", methods=["POST"])
def accounts():
    """
    Register an account
    :return: JSON
    """
    errors = {}
    if not request.json:
        abort(400)

    if 'nickname' not in request.json:
        errors["nickname"] = ["nickname is missing"]
    if 'email' not in request.json:
        errors["email"] = ["email is missing"]
    if 'fullname' not in request.json:
        errors['fullname'] = ['fullname is missing']
    if 'password' not in request.json:
        errors['password'] = ['password is missing']
    if 'confirm' not in request.json:
        errors['confirm'] = ['password confirm is missing']
    if 'agreement' not in request.json:
        errors['agreement'] = ['agreement is missing']

    if len(errors) > 0:
        return jsonify({"error": errors}), 400

    if request.json['password'] != request.json['confirm']:
        return jsonify({"error": {"confirm": ["passwords doesn't match"]}}), 400

    if 'agreement' not in request.json:
        return jsonify({"error": {"agreement": ["you need to accept the terms and conditions"]}}), 400

    # Check if user already exists by username
    user = User.query.filter(User.name == request.json['username']).first()
    if user:
        return jsonify({"error": {"ap_id": ["has already been taken"]}}), 400

    # Check if user already exists by email
    user = User.query.filter(User.email == request.json['email']).first()
    if user:
        return jsonify({"error": {"email": ["has already been taken"]}}), 400

    # Proceed to register the user
    role = Role.query.filter(Role.name == "user").first()
    if not role:
        return jsonify({'error': 'server error'}), 500

    u = user_datastore.create_user(
        name=request.json['username'],
        email=request.json['email'],
        display_name=request.json['fullname'],
        password=encrypt_password(request.json['password']),
        roles=[role]
    )

    actor = create_actor(u)
    actor.user = u
    actor.user_id = u.id
    if 'bio' in request.json:
        actor.summary = request.json['bio']

    db.session.add(actor)
    db.session.commit()

    if FSConfirmable.requires_confirmation(u):
        FSConfirmable.send_confirmation_instructions(u)

    token = authorization.generate_token("reel2bits_frontend", "password", user=u, scope="read write follow push",
                                         expires_in=None)

    tok = OAuth2Token()
    tok.user_id = u.id
    tok.client_id = f'autogen_registration_${datetime.datetime.utcnow()}'  # FIXME
    # the frontend should request an app every time it doesn't have one in local storage
    # and this app should allow delivering a somewhat non usuable Token
    # token which gets sent to this endpoint and gets used to get back the right client_id
    # to associate in the database...
    tok.token_type = token['token_type']
    tok.access_token = token['access_token']
    tok.refresh_token = None
    tok.scope = token['scope']
    tok.revoked = False
    tok.expires_in = token['expires_in']
    db.session.add(tok)
    db.session.commit()

    return jsonify({
        **token,
        'created_at': tok.issued_at
    }), 200
