from flask import Blueprint, render_template, flash, redirect, url_for

from models import User, Config

bp_main = Blueprint('bp_main', __name__)


# Show public logbooks
@bp_main.route('/')
def home():
    _config = Config.query.one()
    if not _config:
        flash("Config not found", 'error')
        return redirect(url_for("bp_main.home"))

    pcfg = {"title": "Home", "app_name": _config.app_name}
    users = User.query.all()

    return render_template('home.jinja2', pcfg=pcfg, users=users)


@bp_main.route('/about')
def about():
    _config = Config.query.one()
    if not _config:
        flash("Config not found", 'error')
        return redirect(url_for("bp_main.home"))

    pcfg = {"title": _config.app_name}

    return render_template('about.jinja2', pcfg=pcfg)
