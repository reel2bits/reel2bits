import pytz
from flask import Blueprint, render_template, request, \
    redirect, url_for, flash, Response, json, jsonify
from flask_babelex import gettext
from flask_security import login_required, current_user

from forms import UserProfileForm
from models import db, User, UserLogging, Sound, Album
from utils import add_user_log
from flask_accept import accept_fallback

bp_users = Blueprint('bp_users', __name__)


@bp_users.route('/account/logs', methods=['GET'])
@login_required
def logs():
    level = request.args.get('level')
    pcfg = {"title": gettext("User Logs")}
    if level:
        _logs = UserLogging.query.filter(UserLogging.level == level.upper(),
                                         UserLogging.user_id == current_user.id
                                         ).limit(100).all()
    else:
        _logs = UserLogging.query.filter(UserLogging.user_id == current_user.id
                                         ).limit(100).all()
    return render_template('users/user_logs.jinja2', pcfg=pcfg, logs=_logs)


@bp_users.route('/account/logs/<int:log_id>/delete',
                methods=['GET', 'DELETE', 'PUT'])
@login_required
def logs_delete(log_id):
    log = UserLogging.query.filter(UserLogging.id == log_id,
                                   UserLogging.user_id == current_user.id
                                   ).first()
    if not log:
        _datas = {"status": "error", "id": log_id}
    else:
        db.session.delete(log)
        db.session.commit()
        _datas = {"status": "deleted", "id": log_id}
    return Response(json.dumps(_datas),
                    mimetype='application/json;charset=utf-8')


@bp_users.route('/user/<string:name>', methods=['GET'])
@accept_fallback
def profile(name):
    pcfg = {"title": gettext(u"%(value)s' profile", value=name)}

    user = User.query.filter(User.name == name).first()
    if not user:
        flash(gettext("User not found"), 'error')
        return redirect(url_for("bp_main.home"))

    if current_user.is_authenticated and user.id == current_user.id:
        sounds = Sound.query.filter(Sound.user_id == user.id)
    else:
        sounds = Sound.query.filter(
            Sound.user_id == user.id,
            Sound.private.is_(False),
            Sound.transcode_state == Sound.TRANSCODE_DONE)

    return render_template('users/profile.jinja2', pcfg=pcfg,
                           user=user, sounds=sounds)


@bp_users.route('/user/<string:name>', methods=['GET'])
@profile.support('application/json', 'application/activity+json')
def actor_json(name):
    user = User.query.filter(User.name == name).first()
    if not user:
        return Response("", status=404)
    actors = user.actor
    if len(actors) <= 0:
        return Response("", status=500)
    actor = actors[0]

    resp = {
        "@context": [
            "https://www.w3.org/ns/activitystreams",
            "https://w3id.org/security/v1"
        ],
        "id": actor.url,
        "type": actor.type.code,
        "preferredUsername": actor.preferred_username,
        "inbox": actor.inbox_url,
        "outbox": actor.outbox_url,
        "manuallyApprovesFollowers": actor.manually_approves_followers,
        "publicKey": {
            "id": actor.private_key_id(),
            "owner": actor.url,
            "publicKeyPem": actor.public_key
        },
        "endpoints": {
            "sharedInbox": actor.shared_inbox_url
        }
    }

    response = jsonify(resp)
    response.mimetype = "application/activity+json; charset=utf-8"
    return response


@bp_users.route('/user/<string:name>/sets', methods=['GET'])
def profile_albums(name):
    pcfg = {"title": gettext(u"%(value)s' profile", value=name)}

    user = User.query.filter(User.name == name).first()
    if not user:
        flash(gettext("User not found"), 'error')
        return redirect(url_for("bp_main.home"))

    if current_user.is_authenticated and user.id == current_user.id:
        albums = Album.query.filter(Album.user_id == user.id)
    else:
        albums = Album.query.filter(Album.user_id == user.id,
                                    Album.private.is_(False))

    return render_template('users/profile_albums.jinja2',
                           pcfg=pcfg, user=user, albums=albums)


@bp_users.route('/account/edit', methods=['GET', 'POST'])
@login_required
def edit():
    pcfg = {"title": gettext("Edit my profile")}

    user = User.query.filter(User.id == current_user.id).first()
    if not user:
        flash(gettext("User not found"), 'error')
        return redirect(url_for("bp_main.home"))

    form = UserProfileForm(request.form, obj=user)
    form.timezone.choices = [[str(i), str(i)] for i in pytz.all_timezones]

    if form.validate_on_submit():
        user.lastname = form.lastname.data
        user.firstname = form.firstname.data
        user.timezone = form.timezone.data
        user.locale = form.locale.data

        db.session.commit()

        # log
        add_user_log(user.id, user.id, 'user', 'info',
                     "Edited user profile")

        flash(gettext("Profile updated"), "success")

        return redirect(url_for('bp_users.profile', name=user.name))

    return render_template('users/edit.jinja2', pcfg=pcfg,
                           form=form, user=user)
