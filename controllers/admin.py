from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    Response,
    json,
)
from flask_babelex import gettext
from flask_security import login_required

from forms import ConfigForm
from models import db, Logging, Config
from utils import is_admin

bp_admin = Blueprint("bp_admin", __name__)


@bp_admin.route("/admin/logs", methods=["GET"])
@login_required
def logs():
    if not is_admin():
        return redirect(url_for("bp_home.home"))
    pcfg = {"title": gettext("Application Logs")}
    _logs = Logging.query.limit(100).all()
    return render_template("admin/logs.jinja2", pcfg=pcfg, logs=_logs)


@bp_admin.route("/admin/logs/<int:log_id>/delete", methods=["GET", "DELETE", "PUT"])
@login_required
def logs_delete(log_id):
    if not is_admin():
        _datas = {"status": "error", "id": log_id}
    else:
        log = Logging.query.filter(Logging.id == log_id).first()
        if not log:
            _datas = {"status": "error", "id": log_id}
        else:
            db.session.delete(log)
            db.session.commit()
            _datas = {"status": "deleted", "id": log_id}
    return Response(json.dumps(_datas), mimetype="application/json;charset=utf-8")


@bp_admin.route("/admin/config", methods=["GET", "POST"])
@login_required
def config():
    if not is_admin():
        return redirect(url_for("bp_main.home"))

    pcfg = {"title": gettext("Application Config")}

    _config = Config.query.one()
    if not _config:
        flash(gettext("Config not found"), "error")
        return redirect(url_for("bp_main.home"))

    form = ConfigForm(request.form, obj=_config)

    if form.validate_on_submit():
        _config.app_name = form.app_name.data
        _config.app_description = form.app_description.data

        db.session.commit()
        flash(gettext("Configuration updated"), "info")
        return redirect(url_for("bp_admin.config"))

    return render_template("admin/config.jinja2", pcfg=pcfg, form=form)
