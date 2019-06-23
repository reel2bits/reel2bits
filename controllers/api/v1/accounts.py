from flask import Blueprint, request, jsonify, abort
from models import db, User, user_datastore, Role, create_actor
from flask_security.utils import encrypt_password
from flask_security import confirmable as FSConfirmable
from oauth import authorization

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
    if not request.json \
            or 'nickname' not in request.json \
            or 'email' not in request.json \
            or 'fullname' not in request.json \
            or 'password' not in request.json \
            or 'agreement' not in request.json:
        abort(400)

    if request.json['password'] != request.json['confirm']:
        return jsonify({'error': 'passwords doesn\'t match'}), 400

    if request.json['nickname'] != request.json['username']:
        return jsonify({'error': 'username doesnt match nickname'}), 400

    if 'confirm' not in request.json:
        return jsonify({'error': 'you need to accepts the terms and condition to register'}), 400

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

    token = authorization.generate_token("reel2bits_frontend", "password", user=u, scope="read write follow push", expires_in=None)
    print(token)
    derp

    # WTF DO I RETURN
    return jsonify({
        'token_type': 'Bearer',
        'access_token': None,
        'scope': 'read write follow push',
        'created_at': None
    }), 200
