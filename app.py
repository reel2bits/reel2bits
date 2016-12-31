# encoding: utf-8
import logging
import os
import subprocess
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template, g, send_from_directory, jsonify
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_migrate import Migrate
from flask_security import Security
from flask_uploads import configure_uploads, UploadSet, IMAGES

from controllers.admin import bp_admin
from controllers.main import bp_main
from controllers.users import bp_users
from forms import ExtendedRegisterForm
from models import db, user_datastore
from utils import dt_utc_to_user_tz, InvalidUsage, show_date_no_offset, is_admin, gcfg

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
    app.jinja_env.globals.update(gcfg=gcfg)

    # Logging
    if not app.debug:
        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
        file_handler = RotatingFileHandler("%s/errors_app.log" % os.getcwd(), 'a', 1000000, 1)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)

    mail = Mail(app)
    migrate = Migrate(app, db)

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

    @app.before_request
    def before_request():
        g.cfg = {
            'REEL2BITS_VERSION_VER': __VERSION__,
            'REEL2BITS_VERSION_GIT': git_version,
            'REEL2BITS_VERSION': "{0} ({1})".format(__VERSION__, git_version),
        }

    @app.errorhandler(InvalidUsage)
    def handle_invalid_usage(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    pictures = UploadSet('pictures', IMAGES)
    configure_uploads(app, pictures)

    app.register_blueprint(bp_main)
    app.register_blueprint(bp_users)
    app.register_blueprint(bp_admin)

    # Used in development
    @app.route('/uploads/<path:stuff>', methods=['GET'])
    def get_uploads_stuff(stuff):
        print("Get {0} from {1}".format(stuff, app.config['UPLOADS_DEFAULT_DEST']))
        return send_from_directory(app.config['UPLOADS_DEFAULT_DEST'], stuff, as_attachment=False)

    @app.errorhandler(404)
    def page_not_found(msg):
        pcfg = {"title": "Whoops, something failed.",
                "error": 404, "message": "Page not found", "e": msg}
        return render_template('error_page.jinja2', pcfg=pcfg), 404

    @app.errorhandler(403)
    def err_forbidden(msg):
        pcfg = {"title": "Whoops, something failed.",
                "error": 403, "message": "Access forbidden", "e": msg}
        return render_template('error_page.jinja2', pcfg=pcfg), 403

    @app.errorhandler(410)
    def err_gone(msg):
        pcfg = {"title": "Whoops, something failed.",
                "error": 410, "message": "Gone", "e": msg}
        return render_template('error_page.jinja2', pcfg=pcfg), 410

    if not app.debug:
        @app.errorhandler(500)
        def err_failed(msg):
            pcfg = {"title": "Whoops, something failed.", "error": 500, "message": "Something is broken", "e": msg}
            return render_template('error_page.jinja2', pcfg=pcfg), 500

    return app
