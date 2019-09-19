from flask import Blueprint, render_template
from flask_babelex import gettext

from models import User

bp_main = Blueprint("bp_main", __name__)


# Show public logbooks
@bp_main.route("/home")
def home():
    pcfg = {"title": gettext("Home")}
    users = User.query.all()

    return render_template("home.jinja2", pcfg=pcfg, users=users)
