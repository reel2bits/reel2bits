from flask import Blueprint, render_template, request, \
    redirect, url_for, flash, current_app
from flask_babelex import gettext

from models import User
from little_boxes.webfinger import get_actor_url
from little_boxes.urlutils import InvalidURLError
from little_boxes import activitypub as ap
from urllib.parse import urlparse

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
        try:
            remote_actor_url = get_actor_url(who, debug=current_app.debug)
        except InvalidURLError:
            current_app.logger.exception(f"Invalid webfinger URL: {who}")
            remote_actor_url = None

        if not remote_actor_url:
            flash(gettext("User not found"), 'error')
            return redirect(url_for("bp_main.home"))

        # We need to get the remote Actor
        backend = ap.get_backend()
        iri = backend.fetch_iri(remote_actor_url)
        if not iri:
            flash(gettext("User not found"), 'error')
            return redirect(url_for("bp_main.home"))

        domain = urlparse(iri['url'])
        user = {
            'name': iri['preferredUsername'],
            'instance': domain.netloc,
            'url': iri['url']
        }

        return render_template('search/remote_user.jinja2', pcfg=pcfg,
                               who=who, user=user)
