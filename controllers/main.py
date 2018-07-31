from flask import Blueprint, render_template, flash, redirect, url_for
from flask_babel import lazy_gettext

from models import User, Config

bp_main = Blueprint('bp_main', __name__)


# Show public logbooks
@bp_main.route('/')
def home():
    pcfg = {"title": lazy_gettext("Home")}
    users = User.query.all()

    return render_template('home.jinja2', pcfg=pcfg, users=users)


@bp_main.route('/about')
def about():
    return render_template('about.jinja2')
