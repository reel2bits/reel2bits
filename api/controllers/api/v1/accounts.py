from flask import Blueprint, request, jsonify, abort, current_app
from models import (
    db,
    User,
    user_datastore,
    Role,
    create_actor,
    OAuth2Token,
    OAuth2Client,
    Activity,
    Sound,
    Follower,
    PasswordResetToken,
    Actor,
    Config,
)
from flask_security.utils import hash_password
from flask_security import confirmable as FSConfirmable
from app_oauth import authorization, require_oauth
from authlib.integrations.flask_oauth2 import current_token
from datas_helpers import to_json_track, to_json_account, to_json_relationship
from utils.various import forbidden_username, add_user_log, add_log, get_hashed_filename
from tasks import send_update_profile, federate_delete_actor, post_to_outbox
import re
from sqlalchemy import or_
import sqlalchemy.exc
from flask_mail import Message
from flask import render_template
import smtplib
from utils.defaults import Reel2bitsDefaults
from flask_uploads import UploadSet
import os
import little_boxes.activitypub as ap


bp_api_v1_accounts = Blueprint("bp_api_v1_accounts", __name__)

username_is_legal = re.compile("^[a-zA-Z0-9]+$")
avatars = UploadSet("avatars", Reel2bitsDefaults.avatar_extensions_allowed)

# Parameters needed:
#  nickname(==username), email, fullname, password, confirm, agreement, locale(dropped here for now)
# Optionals:
#  bio


@bp_api_v1_accounts.route("/api/v1/accounts", methods=["POST"])
def accounts():
    """
    Register an account
    The method is available to apps with a token obtained via the client credentials grant.
    It creates a user and account records, as well as an access token for the app that initiated the request.
    The method returns the access token, which the app should save for later.
    ---
    tags:
        - Accounts
    definitions:
      Token:
        type: object
        properties:
            access_token:
                type: string
            token_type:
                type: string
            scope:
                type: string
            created_at:
                type: integer
    responses:
      200:
        description: Returns Token
        schema:
            $ref: '#/definitions/Token'
    """

    if not current_app.config["REGISTRATION_ENABLED"]:
        abort(403)

    errors = {}

    # Get the bearer token
    bearer = None
    if "Authorization" in request.headers:
        b = request.headers.get("Authorization")
        b = b.strip().split(" ")
        if len(b) == 2:
            bearer = b[1]
        else:
            errors["bearer"] = ["API Bearer Authorization format issue"]
    else:
        current_app.logger.info("/api/v1/accounts: no Authorization bearer given")

    if not request.json:
        abort(400)

    if "nickname" not in request.json:
        errors["nickname"] = ["nickname is missing"]
    if "email" not in request.json:
        errors["email"] = ["email is missing"]
    if "fullname" not in request.json:
        errors["fullname"] = ["fullname is missing"]
    if "password" not in request.json:
        errors["password"] = ["password is missing"]
    if "confirm" not in request.json:
        errors["confirm"] = ["password confirm is missing"]
    if "agreement" not in request.json:
        errors["agreement"] = ["agreement is missing"]

    if len(errors) > 0:
        return jsonify({"error": str(errors)}), 400

    if forbidden_username(request.json["nickname"]):
        return jsonify({"error": str({"nickname": ["this username cannot be used"]})}), 400

    if request.json["password"] != request.json["confirm"]:
        return jsonify({"error": str({"confirm": ["passwords doesn't match"]})}), 400

    if "agreement" not in request.json:
        return jsonify({"error": str({"agreement": ["you need to accept the terms and conditions"]})}), 400

    # Check if user already exists by local user username
    user = User.query.filter(User.name == request.json["username"]).first()
    if user:
        return jsonify({"error": str({"ap_id": ["has already been taken"]})}), 400

    # Check if user already exists by old local user (Actors)
    user = Actor.query.filter(Actor.preferred_username == request.json["username"]).first()
    if user:
        return jsonify({"error": str({"ap_id": ["has already been taken"]})}), 400

    # Check if user already exists by email
    user = User.query.filter(User.email == request.json["email"]).first()
    if user:
        return jsonify({"error": str({"email": ["has already been taken"]})}), 400

    # Check username is valid
    # /^[a-zA-Z\d]+$/
    if not username_is_legal.match(request.json["username"]):
        return jsonify({"error": str({"ap_id": ["should contains only letters and numbers"]})}), 400

    # Proceed to register the user
    role = Role.query.filter(Role.name == "user").first()
    if not role:
        return jsonify({"error": "server error"}), 500

    u = user_datastore.create_user(
        name=request.json["username"],
        email=request.json["email"],
        display_name=request.json["fullname"],
        password=hash_password(request.json["password"]),
        roles=[role],
    )

    actor = create_actor(u)
    actor.user = u
    actor.user_id = u.id
    if "bio" in request.json:
        actor.summary = request.json["bio"]

    db.session.add(actor)
    db.session.commit()

    if FSConfirmable.requires_confirmation(u):
        FSConfirmable.send_confirmation_instructions(u)
        return jsonify({"need_confirmation": True, "message": "need email confirmation"}), 200

    # get the matching item from the given bearer
    bearer_item = OAuth2Token.query.filter(OAuth2Token.access_token == bearer).first()
    if not bearer_item:
        abort(400)
    client_item = OAuth2Client.query.filter(OAuth2Client.client_id == bearer_item.client_id).first()
    if not client_item:
        abort(400)

    # https://github.com/lepture/authlib/blob/master/authlib/oauth2/rfc6749/grants/base.py#L51
    token = authorization.generate_token(
        client_item.client_id, "client_credentials", user=u, scope=client_item.scope, expires_in=None
    )

    tok = OAuth2Token()
    tok.user_id = u.id
    tok.client_id = client_item.client_id
    # the frontend should request an app every time it doesn't have one in local storage
    # and this app should allow delivering a somewhat non usuable Token
    # token which gets sent to this endpoint and gets used to get back the right client_id
    # to associate in the database...
    tok.token_type = token["token_type"]
    tok.access_token = token["access_token"]
    tok.refresh_token = None
    tok.scope = token["scope"]
    tok.revoked = False
    tok.expires_in = token["expires_in"]
    db.session.add(tok)
    db.session.commit()

    return jsonify({**token, "created_at": tok.issued_at}), 200


@bp_api_v1_accounts.route("/api/v1/accounts/<string:username_or_id>", methods=["GET"])
@require_oauth(optional=True)
def account_get(username_or_id):
    """
    Returns Account
    ---
    tags:
        - Accounts
    responses:
      200:
        description: Returns Account
        schema:
            $ref: '#/definitions/Account'
    """
    user = User.query.filter(User.name == username_or_id, User.local.is_(True)).first()
    if not user:
        try:
            user = User.query.filter(User.flake_id == username_or_id).first()
        except sqlalchemy.exc.DataError:
            abort(404)

    if not user:
        abort(404)
    if len(user.actor) != 1:
        abort(404)

    relationship = False
    if current_token and current_token.user:
        relationship = to_json_relationship(current_token.user, user)
    account = to_json_account(user, relationship)
    return jsonify(account)


@bp_api_v1_accounts.route("/api/v1/accounts/verify_credentials", methods=["GET"])
@require_oauth("read")
def accounts_verify_credentials():
    """
    User’s own account.
    ---
    tags:
        - Accounts
    security:
        - OAuth2:
            - read
    definitions:
      Field:
        type: object
        properties:
            name:
                type: string
                nullable: false
            value:
                type: string
                nullable: false
            verified_at:
                type: integer
                nullable: true
      Emoji:
        type: object
        properties:
            shortcode:
                type: string
                nullable: false
            static_url:
                type: string
                format: uri
                nullable: false
            url:
                type: string
                format: uri
                nullable: false
            visible_in_picker:
                type: boolean
                nullable: false
      Source:
        type: object
        properties:
            privacy:
                type: string
                nullable: true
            sensitive:
                type: boolean
                nullable: true
            language:
                type: string
                nullable: true
            note:
                type: string
                nullable: false
            fields:
                type: array
                nullable: false
                items:
                    type: object
                    $ref: '#/definitions/Field'
      AccountPleroma:
        type: object
        properties:
            pleroma:
                type: object
                properties:
                    is_admin:
                        type: boolean
      Account:
        type: object
        properties:
            id:
                type: string
                nullable: false
            username:
                type: string
                nullable: false
            acct:
                type: string
                nullable: false
            display_name:
                type: integer
                nullable: false
            locked:
                type: boolean
                nullable: false
            created_at:
                type: integer
                nullable: false
            followers_count:
                type: integer
                nullable: false
            following_count:
                type: integer
                nullable: false
            statuses_count:
                type: integer
                nullable: false
            note:
                type: string
                nullable: false
            url:
                type: string
                format: uri
                nullable: false
            avatar:
                type: string
                format: uri
                nullable: false
            avatar_static:
                type: string
                format: uri
                nullable: false
            header:
                type: string
                format: uri
                nullable: false
            header_static:
                type: string
                format: uri
                nullable: false
            emojis:
                type: hash
                nullable: false
                items:
                    type: object
                    $ref: '#/definitions/Emoji'
            moved:
                type: object
                $ref: '#/definitions/Account'
                nullable: true
            fields:
                type: array
                nullable: true
                items:
                    type: object
                    $ref: '#/definitions/Field'
            bot:
                type: boolean
                nullable: true
    responses:
        200:
            description: Returns Account with extra Source and Pleroma attributes.
            schema:
                allOf:
                    - $ref: '#/definitions/Account'
                    - $ref: '#/definitions/Source'
                    - $ref: '#/definitions/AccountPleroma'
    """
    user = current_token.user
    return jsonify(to_json_account(user))


@bp_api_v1_accounts.route("/api/v1/accounts/update_credentials", methods=["PATCH"])
@require_oauth("write")
def accounts_update_credentials():
    """
    Update user’s own account.
    ---
    tags:
        - Accounts
    security:
        - OAuth2:
            - write
    responses:
        200:
            description: Returns Account with extra Source and Pleroma attributes.
            schema:
                allOf:
                    - $ref: '#/definitions/Account'
                    - $ref: '#/definitions/Source'
                    - $ref: '#/definitions/AccountPleroma'
    """
    current_user = current_token.user

    if not current_user:
        # WTF ?
        return jsonify({"error": "User not found"}), 404

    # Update fields like bio, language, etc.
    if request.json:
        r_lang = request.json.get("lang", None)
        r_fullname = request.json.get("fullname", None)
        r_bio = request.json.get("bio", None)

        if r_lang:
            current_user.locale = r_lang
        if r_fullname:
            current_user.display_name = r_fullname
        if r_bio:
            current_user.actor[0].summary = r_bio
    elif request.files:
        # Update things like user background, profile picture, etc.
        if "avatar" in request.files:
            avatar_uploaded = request.files["avatar"]
            avatar_uploaded.seek(0, os.SEEK_END)
            avatar_size = avatar_uploaded.tell()
            avatar_uploaded.seek(0)
            if avatar_size > Reel2bitsDefaults.avatar_size_limit:
                return jsonify({"error": "artwork too big, 2MB maximum"}), 413  # Request Entity Too Large

            # Delete old avatar if any
            if current_user.avatar_filename:
                old_avatar = os.path.join(current_app.config["UPLOADED_AVATARS_DEST"], current_user.path_avatar())
                if os.path.isfile(old_avatar):
                    os.unlink(old_avatar)
                else:
                    print(f"Error: cannot delete old avatar: {current_user.id} / {current_user.avatar_filename}")

            # Save new avatar
            avatar_filename = get_hashed_filename(avatar_uploaded.filename)
            avatars.save(avatar_uploaded, folder=current_user.slug, name=avatar_filename)
            current_user.avatar_filename = avatar_filename

    # commit changes
    db.session.commit()

    # log action
    add_user_log(current_user.id, current_user.id, "user", "info", "Edited user profile")

    # trigger a profile update
    send_update_profile(current_user)

    return jsonify(to_json_account(current_user))


@bp_api_v1_accounts.route("/api/v1/accounts/<string:username_or_id>/statuses", methods=["GET"])
@require_oauth(optional=True)
def user_statuses(username_or_id):
    """
    User statuses.
    ---
    tags:
        - Timelines
    parameters:
        - name: count
          in: query
          type: integer
          required: true
          description: count per page
        - name: with_muted
          in: query
          type: boolean
          required: true
          description: with muted users
        - name: page
          in: query
          type: integer
          description: page number
    responses:
        200:
            description: Returns array of Status
    """
    # Caveats: only handle public Sounds since we either federate (public) or no
    count = int(request.args.get("count", 20))
    page = int(request.args.get("page", 1))

    # Get associated user
    user = User.query.filter(User.name == username_or_id, User.local.is_(True)).first()
    if not user:
        try:
            user = User.query.filter(User.flake_id == username_or_id).first()
        except sqlalchemy.exc.DataError:
            abort(404)
    if not user:
        abort(404)

    q = db.session.query(Activity, Sound).filter(
        Activity.type == "Create", Activity.payload[("object", "type")].astext == "Audio"
    )
    q = q.filter(Activity.meta_deleted.is_(False))

    q = q.filter(Activity.payload["to"].astext.contains("https://www.w3.org/ns/activitystreams#Public"))

    q = q.filter(Activity.actor_id == user.actor[0].id)

    q = q.join(Sound, Sound.activity_id == Activity.id)
    q = q.order_by(Activity.creation_date.desc())

    q = q.paginate(page=page, per_page=count)

    tracks = []
    for t in q.items:
        if t.Sound:
            relationship = False
            if current_token and current_token.user:
                relationship = to_json_relationship(current_token.user, t.Sound.user)
            account = to_json_account(t.Sound.user, relationship)
            tracks.append(to_json_track(t.Sound, account))
        else:
            print(t.Activity)
    resp = {"page": page, "page_size": count, "totalItems": q.total, "items": tracks, "totalPages": q.pages}
    return jsonify(resp)


@bp_api_v1_accounts.route("/api/v1/accounts/relationships", methods=["GET"])
@bp_api_v1_accounts.route("/api/v1/accounts/relationships/", methods=["GET"])
@require_oauth("read")
def relationships():
    """
    Relationship of the user to the given accounts in regards to following, blocking, muting, etc.
    ---
    tags:
        - Accounts
    definitions:
      Relationship:
        type: object
        properties:
            id:
                type: string
                nullable: false
            following:
                type: boolean
                nullable: false
            followed_by:
                type: boolean
                nullable: false
            blocking:
                type: boolean
                nullable: false
            muting:
                type: boolean
                nullable: false
            muting_notifications:
                type: boolean
                nullable: false
            requested:
                type: boolean
                nullable: false
            domain_blocking:
                type: boolean
                nullable: false
            showing_reblogs:
                type: boolean
                nullable: false
            endorsed:
                type: boolean
                nullable: false
    parameters:
        - name: id
          in: query
          type: array
          required: true
          items:
            type: integer
          description: Array of account IDs
    responses:
      200:
        description: Returns array of Relationship
        schema:
            $ref: '#/definitions/Relationship'
    """
    flake_ids = request.args.getlist("id")
    of_user = current_token.user

    rels = []
    for id in flake_ids:
        against_user = User.query.filter(User.flake_id == id).first()
        if not against_user:
            if len(flake_ids) > 1:
                next
            else:
                return jsonify([])
        rels.append(to_json_relationship(of_user, against_user))
    return jsonify(rels)


@bp_api_v1_accounts.route("/api/v1/accounts/<string:username_or_id>/follow", methods=["POST"])
@require_oauth("write")
def follow(username_or_id):
    """
    Follow an account.
    ---
    tags:
        - Accounts
    parameters:
        - name: id
          in: query
          type: integer
          required: true
          description: User ID to follow
    responses:
      200:
        description: Returns Relationship
        schema:
            $ref: '#/definitions/Relationship'
    """
    current_user = current_token.user
    if not current_user:
        abort(400)

    user = User.query.filter(User.name == username_or_id, User.local.is_(True)).first()
    if not user:
        try:
            user = User.query.filter(User.flake_id == username_or_id).first()
        except sqlalchemy.exc.DataError:
            abort(404)
    if not user:
        abort(404)

    actor_me = current_user.actor[0]
    actor_them = user.actor[0]

    if user.local:
        actor_me.follow(None, actor_them)
        return jsonify([to_json_relationship(current_user, user)])
    else:
        # We need to initiate a follow request
        # Check if not already following
        rel = Follower.query.filter(Follower.actor_id == actor_me.id, Follower.target_id == actor_them.id).first()

        if not rel:
            # Initiate a Follow request from actor_me to actor_target
            follow = ap.Follow(actor=actor_me.url, object=actor_them.url)
            post_to_outbox(follow)
            return jsonify(""), 202
        else:
            return jsonify({"error": "already following"}), 409


@bp_api_v1_accounts.route("/api/v1/accounts/<string:username_or_id>/unfollow", methods=["POST"])
@require_oauth("write")
def unfollow(username_or_id):
    """
    Unfollow an account.
    ---
    tags:
        - Accounts
    parameters:
        - name: id
          in: path
          type: integer
          required: true
          description: User ID to follow
    responses:
      200:
        description: Returns Relationship
        schema:
            $ref: '#/definitions/Relationship'
    """
    current_user = current_token.user
    if not current_user:
        abort(400)

    user = User.query.filter(User.name == username_or_id, User.local.is_(True)).first()
    if not user:
        try:
            user = User.query.filter(User.flake_id == username_or_id).first()
        except sqlalchemy.exc.DataError:
            abort(404)
    if not user:
        abort(404)

    actor_me = current_user.actor[0]
    actor_them = user.actor[0]

    if user.local:
        actor_me.unfollow(actor_them)
        return jsonify([to_json_relationship(current_user, user)])
    else:
        # Get the relation of the follow
        follow_relation = Follower.query.filter(
            Follower.actor_id == actor_me.id, Follower.target_id == actor_them.id
        ).first()
        if not follow_relation:
            return jsonify({"error": "follow relation not found"}), 404

        # Fetch the related Activity of the Follow relation
        accept_activity = Activity.query.filter(Activity.url == follow_relation.activity_url).first()
        if not accept_activity:
            current_app.logger.error(f"cannot find accept activity {follow_relation.activity_url}")
            return jsonify({"error": "cannot found the accept activity"}), 500
        # Then the Activity ID of the ACcept will be the object id
        activity = ap.parse_activity(payload=accept_activity.payload)

        # get the final activity (the Follow one)
        follow_activity = Activity.query.filter(Activity.url == activity.get_object_id()).first()
        if not follow_activity:
            current_app.logger.error(f"cannot find follow activity {activity.get_object_id()}")
            return jsonify({"error": "cannot find follow activity"}), 500

        ap_follow_activity = ap.parse_activity(payload=follow_activity.payload)

        # initiate an Undo of the Follow request
        unfollow = ap_follow_activity.build_undo()
        post_to_outbox(unfollow)
        return jsonify(""), 202


@bp_api_v1_accounts.route("/api/v1/accounts/<string:username_or_id>/followers", methods=["GET"])
@require_oauth(optional=True)
def followers(username_or_id):
    """
    Accounts which follow the given account.
    ---
    tags:
        - Accounts
    parameters:
        - name: id
          in: path
          type: integer
          required: true
          description: User ID to follow
        - name: count
          in: query
          type: integer
          required: true
          description: count per page
        - name: page
          in: query
          type: integer
          description: page number
    responses:
      200:
        description: Returns paginated array of Account
        schema:
            $ref: '#/definitions/Account'
    """
    user = User.query.filter(User.name == username_or_id, User.local.is_(True)).first()
    if not user:
        try:
            user = User.query.filter(User.flake_id == username_or_id).first()
        except sqlalchemy.exc.DataError:
            abort(404)
    if not user:
        abort(404)

    count = int(request.args.get("count", 20))
    page = int(request.args.get("page", 1))

    q = user.actor[0].followers
    q = q.paginate(page=page, per_page=count)

    followers = []
    for t in q.items:
        # Note: the items are Follower(actor, target)
        # Where target is `user` since we are asking his followers
        # And actor = the user following `user`
        relationship = False
        if current_token and current_token.user:
            relationship = to_json_relationship(current_token.user, t.actor.user)
        account = to_json_account(t.actor.user, relationship)
        followers.append(account)

    resp = {"page": page, "page_size": count, "totalItems": q.total, "items": followers, "totalPages": q.pages}
    return jsonify(resp)


@bp_api_v1_accounts.route("/api/v1/accounts/<string:username_or_id>/following", methods=["GET"])
@require_oauth(optional=True)
def following(username_or_id):
    """
    Accounts followed by the given account.
    ---
    tags:
        - Accounts
    parameters:
        - name: id
          in: path
          type: integer
          required: true
          description: User ID to follow
        - name: count
          in: query
          type: integer
          required: true
          description: count per page
        - name: page
          in: query
          type: integer
          description: page number
    responses:
      200:
        description: Returns paginated array of Account
        schema:
            $ref: '#/definitions/Account'
    """
    user = User.query.filter(User.name == username_or_id, User.local.is_(True)).first()
    if not user:
        try:
            user = User.query.filter(User.flake_id == username_or_id).first()
        except sqlalchemy.exc.DataError:
            abort(404)
    if not user:
        abort(404)

    count = int(request.args.get("count", 20))
    page = int(request.args.get("page", 1))

    q = user.actor[0].followings
    q = q.paginate(page=page, per_page=count)

    followings = []
    for t in q.items:
        # Note: the items are Follower(actor, target)
        # Where actor is `user` since we are asking his followers
        # And target = the user following `user`
        relationship = False
        if current_token and current_token.user:
            relationship = to_json_relationship(current_token.user, t.target.user)
        account = to_json_account(t.target.user, relationship)
        followings.append(account)

    resp = {"page": page, "page_size": count, "totalItems": q.total, "items": followings, "totalPages": q.pages}
    return jsonify(resp)


@bp_api_v1_accounts.route("/api/v1/accounts", methods=["DELETE"])
@require_oauth("write")
def account_delete():
    """
    Delete account
    ---
    tags:
        - Accounts
    responses:
      200:
        description: Returns user username
    """
    current_user = current_token.user
    if not current_user:
        abort(400)

    # store a few infos
    username = current_user.name
    user_id = current_user.id
    email = current_user.email

    # Revoke Oauth2 credentials
    for oa2_token in OAuth2Token.query.filter(OAuth2Token.user_id == current_user.id).all():
        oa2_token.revoked = True

    # Drop password reset tokens
    for prt in PasswordResetToken.query.filter(PasswordResetToken.user_id == current_user.id).all():
        db.session.delete(prt)

    # set all activities as deleted
    activities = Activity.query.filter(Activity.actor_id == current_user.actor[0].id)
    for activity in activities.all():
        activity.meta_deleted = True

    # set actor as deleted and federate a Delete(Actor)
    current_user.actor[0].meta_deleted = True
    # Federate Delete(Actor)
    federate_delete_actor(current_user.actor[0])

    # drop all relations
    follows = Follower.query.filter(
        or_(Follower.actor_id == current_user.actor[0].id, Follower.target_id == current_user.actor[0].id)
    )
    for follow_rel in follows.all():
        db.session.delete(follow_rel)

    # delete User
    db.session.delete(current_user)

    db.session.commit()  # crimes

    # send email that account have been deleted
    msg = Message(
        subject="Account successfully deleted", recipients=[email], sender=current_app.config["MAIL_DEFAULT_SENDER"]
    )

    _config = Config.query.first()
    if not _config:
        print("ERROR: cannot get instance Config from database")
    instance = {"name": None, "url": None}
    if _config:
        instance["name"] = _config.app_name
    instance["url"] = current_app.config["REEL2BITS_URL"]
    msg.body = render_template("email/account_deleted.txt", username=username, instance=instance)
    msg.html = render_template("email/account_deleted.html", username=username, instance=instance)
    err = None
    mail = current_app.extensions.get("mail")
    if not mail:
        err = "mail extension is none"
    else:
        try:
            mail.send(msg)
        except ConnectionRefusedError as e:
            # TODO: do something about that maybe
            print(f"Error sending mail: {e}")
            err = e
        except smtplib.SMTPRecipientsRefused as e:
            print(f"Error sending mail: {e}")
            err = e
        except smtplib.SMTPException as e:
            print(f"Error sending mail: {e}")
            err = e
    if err:
        add_log("global", "ERROR", f"Error sending email for account deletion of {username} ({user_id}): {err}")

    return jsonify({"username": username}), 200
