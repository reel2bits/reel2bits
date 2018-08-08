from flask import Blueprint, render_template, request, \
    redirect, url_for, flash
from flask_babelex import gettext

from models import User
from little_boxes.webfinger import webfinger

bp_search = Blueprint('bp_search', __name__, url_prefix='/search')


@bp_search.route('/users', methods=['GET'])
def users():
    who = request.args.get('who')
    pcfg = {"title": gettext("Search user")}

    # Search is to be done in two steps:
    # 1. Search from local User
    # 2. If not found, webfinger it

    local_users = User.query.filter(User.name.like(who)).all()

    if len(local_users) > 0:
        return render_template('search/local_user.jinja2', pcfg=pcfg,
                               who=who, users=local_users)

    if not local_users:
        remote_user = webfinger(who)
        if not remote_user:
            flash(gettext("User not found"), 'error')
            return redirect(url_for("bp_main.home"))

        return render_template('search/remote_user.jinja2', pcfg=pcfg,
                               who=who, user=remote_user)
