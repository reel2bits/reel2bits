import pytz
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_security import login_required, current_user
from sqlalchemy import func

from forms import UserProfileForm
from models import db, User, UserLogging

bp_users = Blueprint('bp_users', __name__)


@bp_users.route('/user/logs', methods=['GET'])
@login_required
def logs():
    level = request.args.get('level')
    pcfg = {"title": "User Logs"}
    if level:
        _logs = UserLogging.query.filter(UserLogging.level == level.upper(),
                                         UserLogging.user_id == current_user.id
                                         ).order_by(UserLogging.timestamp.desc()).limit(100).all()
    else:
        _logs = UserLogging.query.filter(UserLogging.user_id == current_user.id
                                         ).order_by(UserLogging.timestamp.desc()).limit(100).all()
    return render_template('users/user_logs.jinja2', pcfg=pcfg, logs=_logs)


@bp_users.route('/user/<string:name>', methods=['GET'])
@login_required
def profile(name):
    pcfg = {"title": "%s's profile" % name}

    user = User.query.filter(User.name == name).first()
    if not user:
        flash("User not found", 'error')
        return redirect(url_for("bp_main.home"))

    return render_template('users/profile.jinja2', pcfg=pcfg, user=user)


@bp_users.route('/user/edit', methods=['GET', 'POST'])
@login_required
def edit():
    pcfg = {"title": "Edit my profile"}

    user = User.query.filter(User.id == current_user.id).first()
    if not user:
        flash("User not found", 'error')
        return redirect(url_for("bp_main.home"))

    form = UserProfileForm(request.form, user)
    form.timezone.choices = [[str(i), str(i)] for i in pytz.all_timezones]

    if form.validate_on_submit():
        user.lastname = form.lastname.data
        user.firstname = form.firstname.data
        user.timezone = form.timezone.data

        db.session.commit()
        return redirect(url_for('bp_users.profile'))

    return render_template('users/edit.jinja2', pcfg=pcfg, form=form, user=user)
