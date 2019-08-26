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


# Ugly temporary until the old templates are all removed
bp_vue = Blueprint(
    "bp_vue", __name__, static_folder="front/dist/static/", template_folder="../front/dist/", static_url_path="/static/"
)


@bp_vue.route("/", defaults={"path": ""})
@bp_vue.route("/<path:path>")
def root(path):
    return render_template("index.html")
