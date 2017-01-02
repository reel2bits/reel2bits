# encoding: utf-8
import logging
import os
import subprocess
from logging.handlers import RotatingFileHandler
from flask.ext.babel import lazy_gettext
from flask import Flask, render_template, g, send_from_directory, jsonify, safe_join, request
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_migrate import Migrate
from flask_security import Security
from flask_uploads import configure_uploads, UploadSet, AUDIO
from flask.ext.babel import Babel

from controllers.admin import bp_admin
from controllers.albums import bp_albums
from controllers.main import bp_main
from controllers.sound import bp_sound
from controllers.users import bp_users
from forms import ExtendedRegisterForm
from models import db, user_datastore
from utils import InvalidUsage, is_admin, gcfg, duration_elapsed_human, duration_song_human

__VERSION__ = "0.0.1"


def create_app(cfg=None):
    # App Configuration
    if cfg is None:
        cfg = {}
    app = Flask(__name__)
    app.config.from_pyfile("config.py")
    app.config.update(cfg)

    Bootstrap(app)

    app.jinja_env.add_extension('jinja2.ext.with_')
    app.jinja_env.add_extension('jinja2.ext.do')
    app.jinja_env.globals.update(is_admin=is_admin)
    app.jinja_env.globals.update(duration_elapsed_human=duration_elapsed_human)
    app.jinja_env.globals.update(duration_song_human=duration_song_human)

    # Logging
    if not app.debug:
        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
        file_handler = RotatingFileHandler("%s/errors_app.log" % os.getcwd(), 'a', 1000000, 1)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)

    mail = Mail(app)
    migrate = Migrate(app, db)
    babel = Babel(app)

    db.init_app(app)

    # Setup Flask-Security
    security = Security(app, user_datastore,
                        register_form=ExtendedRegisterForm)

    git_version = ""
    gitpath = os.path.join(os.getcwd(), ".git")
    if os.path.isdir(gitpath):
        git_version = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'])
        if git_version:
            git_version = git_version.strip().decode('UTF-8')

    @babel.localeselector
    def get_locale():
        # if a user is logged in, use the locale from the user settings
        identity = getattr(g, 'identity', None)
        if identity is not None and identity.id:
            return identity.user.locale
        # otherwise try to guess the language from the user accept
        # header the browser transmits.  We support fr/en in this
        # example.  The best match wins.
        return request.accept_languages.best_match(['fr', 'en'])

    @babel.timezoneselector
    def get_timezone():
        identity = getattr(g, 'identity', None)
        if identity is not None and identity.id:
            return identity.user.timezone

    @app.before_request
    def before_request():
        g.cfg = {
            'REEL2BITS_VERSION_VER': __VERSION__,
            'REEL2BITS_VERSION_GIT': git_version,
            'REEL2BITS_VERSION': "{0} ({1})".format(__VERSION__, git_version),
        }.update(gcfg())

    @app.errorhandler(InvalidUsage)
    def handle_invalid_usage(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    sounds = UploadSet('sounds', AUDIO)
    configure_uploads(app, sounds)

    app.register_blueprint(bp_main)
    app.register_blueprint(bp_users)
    app.register_blueprint(bp_admin)
    app.register_blueprint(bp_sound)
    app.register_blueprint(bp_albums)

    # Used in development
    @app.route('/uploads/<string:thing>/<path:stuff>', methods=['GET'])
    def get_uploads_stuff(thing, stuff):
        directory = safe_join(app.config['UPLOADS_DEFAULT_DEST'], thing)
        print("Get {0} from {1}".format(stuff, directory))
        return send_from_directory(directory, stuff, as_attachment=True)

    @app.errorhandler(404)
    def page_not_found(msg):
        pcfg = {"title": lazy_gettext("Whoops, something failed."),
                "error": 404, "message": lazy_gettext("Page not found"), "e": msg}
        return render_template('error_page.jinja2', pcfg=pcfg), 404

    @app.errorhandler(403)
    def err_forbidden(msg):
        pcfg = {"title": lazy_gettext("Whoops, something failed."),
                "error": 403, "message": lazy_gettext("Access forbidden"), "e": msg}
        return render_template('error_page.jinja2', pcfg=pcfg), 403

    @app.errorhandler(410)
    def err_gone(msg):
        pcfg = {"title": lazy_gettext("Whoops, something failed."),
                "error": 410, "message": lazy_gettext("Gone"), "e": msg}
        return render_template('error_page.jinja2', pcfg=pcfg), 410

    if not app.debug:
        @app.errorhandler(500)
        def err_failed(msg):
            pcfg = {"title": lazy_gettext("Whoops, something failed."), "error": 500,
                    "message": lazy_gettext("Something is broken"), "e": msg}
            return render_template('error_page.jinja2', pcfg=pcfg), 500

    return app
