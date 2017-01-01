import pytz
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, json
from flask_security import login_required, current_user
from flask.ext.babel import lazy_gettext, gettext

from forms import UserProfileForm
from models import db, User, UserLogging, Sound

bp_users = Blueprint('bp_users', __name__)


@bp_users.route('/user/logs', methods=['GET'])
@login_required
def logs():
    level = request.args.get('level')
    pcfg = {"title": lazy_gettext("User Logs")}
    if level:
        _logs = UserLogging.query.filter(UserLogging.level == level.upper(),
                                         UserLogging.user_id == current_user.id
                                         ).order_by(UserLogging.timestamp.desc()).limit(100).all()
    else:
        _logs = UserLogging.query.filter(UserLogging.user_id == current_user.id
                                         ).order_by(UserLogging.timestamp.desc()).limit(100).all()
    return render_template('users/user_logs.jinja2', pcfg=pcfg, logs=_logs)


@bp_users.route('/user/logs/<int:log_id>/delete', methods=['GET', 'DELETE', 'PUT'])
@login_required
def logs_delete(log_id):
    log = UserLogging.query.filter(UserLogging.id == log_id, UserLogging.user_id == current_user.id).first()
    if not log:
        _datas = {"status": "error", "id": log_id}
    else:
        db.session.delete(log)
        db.session.commit()
        _datas = {"status": "deleted", "id": log_id}
    return Response(json.dumps(_datas), mimetype='application/json;charset=utf-8')


@bp_users.route('/user/<string:name>', methods=['GET'])
def profile(name):
    pcfg = {"title": gettext(u"%(value)s' profile", value=name)}

    user = User.query.filter(User.name == name).first()
    if not user:
        flash(lazy_gettext("User not found"), 'error')
        return redirect(url_for("bp_main.home"))

    if current_user.is_authenticated and user.id == current_user.id:
        sounds = Sound.query.filter(Sound.user_id == user.id)
    else:
        sounds = Sound.query.filter(Sound.user_id == user.id, Sound.private.is_(False))

    return render_template('users/profile.jinja2', pcfg=pcfg, user=user, sounds=sounds)


@bp_users.route('/user/edit', methods=['GET', 'POST'])
@login_required
def edit():
    pcfg = {"title": lazy_gettext("Edit my profile")}

    user = User.query.filter(User.id == current_user.id).first()
    if not user:
        flash(lazy_gettext("User not found"), 'error')
        return redirect(url_for("bp_main.home"))

    form = UserProfileForm(request.form, user)
    form.timezone.choices = [[str(i), str(i)] for i in pytz.all_timezones]

    if form.validate_on_submit():
        user.lastname = form.lastname.data
        user.firstname = form.firstname.data
        user.timezone = form.timezone.data
        user.locale = form.locale.data

        db.session.commit()
        return redirect(url_for('bp_users.profile', name=user.name))

    return render_template('users/edit.jinja2', pcfg=pcfg, form=form, user=user)
