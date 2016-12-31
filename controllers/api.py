from flask import Blueprint, redirect, url_for, abort, flash
from flask_security import login_required, current_user

from models import db, Apitoken
from utils import generate_uniques_apitoken

bp_api = Blueprint('bp_api', __name__)


@bp_api.route('/api/token/new')
@login_required
def apitoken_new():
    apitoken = generate_uniques_apitoken()
    if not apitoken:
        return abort(500)

    a = Apitoken()
    a.user_id = current_user.id
    a.token = apitoken["token"]
    a.secret = apitoken["secret"]
    db.session.add(a)
    db.session.commit()
    return redirect(url_for('bp_users.user_profile'))


@bp_api.route('/api/token/<string:apit>/del')
@login_required
def apitoken_del(apit):
    apitoken = Apitoken.query.filter(Apitoken.id == apit).first()
    if not apitoken:
        flash("API Token not found", "error")
        return redirect(url_for("bp_main.home"))

    db.session.delete(apitoken)
    db.session.commit()
    return redirect(url_for('bp_users.user_profile'))
