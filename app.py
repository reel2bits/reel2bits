# encoding: utf-8
import logging
import os
import subprocess
from logging.handlers import RotatingFileHandler
from flask_babelex import gettext, Babel
from flask import Flask, render_template, g, send_from_directory, \
    jsonify, safe_join, request, flash
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_migrate import Migrate
from flask_security import Security
from flask_security.utils import encrypt_password
from flask_security import signals as FlaskSecuritySignals
from flask_security import confirmable as FSConfirmable
from flask_uploads import configure_uploads, UploadSet, AUDIO

from controllers.admin import bp_admin
from controllers.albums import bp_albums
from controllers.main import bp_main
from controllers.sound import bp_sound
from controllers.users import bp_users
from controllers.search import bp_search
from controllers.api.v1.well_known import bp_wellknown
from controllers.api.v1.nodeinfo import bp_nodeinfo
from controllers.api.v1.activitypub import bp_ap

from forms import ExtendedRegisterForm
from models import db, Config, user_datastore, Role, create_actor
from utils import InvalidUsage, is_admin, duration_elapsed_human, \
    duration_song_human, add_user_log

import texttable
from flask_debugtoolbar import DebugToolbarExtension

from dbseed import make_db_seed
from pprint import pprint as pp
import click
from little_boxes import activitypub as ap
from activitypub.backend import Reel2BitsBackend

__VERSION__ = "0.0.1"

try:
    from raven.contrib.flask import Sentry
    import raven

    print(" * Sentry support loaded")
    HAS_SENTRY = True
except ImportError as e:
    print(" * No Sentry support")
    HAS_SENTRY = False

mail = Mail()


def create_app(config_filename="config.py"):
    # App configuration
    app = Flask(__name__)
    app.config.from_pyfile(config_filename)

    Bootstrap(app)

    app.jinja_env.add_extension('jinja2.ext.with_')
    app.jinja_env.add_extension('jinja2.ext.do')
    app.jinja_env.globals.update(is_admin=is_admin)
    app.jinja_env.globals.update(duration_elapsed_human=duration_elapsed_human)
    app.jinja_env.globals.update(duration_song_human=duration_song_human)

    if HAS_SENTRY:
        app.config['SENTRY_RELEASE'] = raven.fetch_git_sha(
            os.path.dirname(__file__))
        sentry = Sentry(app, dsn=app.config['SENTRY_DSN'])  # noqa: F841
        print(" * Sentry support activated")
        print(" * Sentry DSN: %s" % app.config['SENTRY_DSN'])

    if app.config['DEBUG'] is True:
        app.jinja_env.auto_reload = True
        app.logger.setLevel(logging.DEBUG)

    # Logging
    if not app.debug:
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]')
        file_handler = RotatingFileHandler(
            "%s/errors_app.log" % os.getcwd(), 'a', 1000000, 1)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)

    mail.init_app(app)
    migrate = Migrate(app, db)  # noqa: F841
    babel = Babel(app)  # noqa: F841
    toolbar = DebugToolbarExtension(app)  # noqa: F841

    db.init_app(app)

    # ActivityPub backend
    back = Reel2BitsBackend()
    ap.use_backend(back)

    # Setup Flask-Security
    security = Security(app, user_datastore,  # noqa: F841
                        register_form=ExtendedRegisterForm,
                        confirm_register_form=ExtendedRegisterForm)

    @FlaskSecuritySignals.password_reset.connect_via(app)
    @FlaskSecuritySignals.password_changed.connect_via(app)
    def log_password_reset(sender, user):
        if not user:
            return
        add_user_log(user.id, user.id, "user", "info",
                     "Your password has been changed !")

    @FlaskSecuritySignals.reset_password_instructions_sent.connect_via(app)
    def log_reset_password_instr(sender, user, token):
        if not user:
            return
        add_user_log(user.id, user.id, "user", "info",
                     "Password reset instructions sent.")

    @FlaskSecuritySignals.user_registered.connect_via(app)
    def create_actor_for_registered_user(app, user, confirm_token):
        if not user:
            return
        actor = create_actor(user)
        actor.user = user
        actor.user_id = user.id
        db.session.add(actor)
        db.session.commit()

    git_version = ""
    gitpath = os.path.join(os.getcwd(), ".git")
    if os.path.isdir(gitpath):
        git_version = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'])
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
        _config = Config.query.first()
        if not _config:
            flash(gettext("Config not found"), 'error')

        cfg = {
            'REEL2BITS_VERSION_VER': __VERSION__,
            'REEL2BITS_VERSION_GIT': git_version,
            'REEL2BITS_VERSION': "{0} ({1})".format(__VERSION__, git_version),
            "app_name": _config.app_name,
            'app_description': _config.app_description
        }
        g.cfg = cfg

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
    app.register_blueprint(bp_search)

    app.register_blueprint(bp_wellknown)
    app.register_blueprint(bp_nodeinfo)
    app.register_blueprint(bp_ap)

    # Used in development
    @app.route('/uploads/<string:thing>/<path:stuff>', methods=['GET'])
    def get_uploads_stuff(thing, stuff):
        directory = safe_join(app.config['UPLOADS_DEFAULT_DEST'], thing)
        print("Get {0} from {1}".format(stuff, directory))
        return send_from_directory(directory, stuff, as_attachment=True)

    @app.errorhandler(404)
    def page_not_found(msg):
        pcfg = {"title": gettext("Whoops, something failed."),
                "error": 404, "message": gettext("Page not found"),
                "e": msg}
        return render_template('error_page.jinja2', pcfg=pcfg), 404

    @app.errorhandler(403)
    def err_forbidden(msg):
        pcfg = {"title": gettext("Whoops, something failed."),
                "error": 403, "message": gettext("Access forbidden"),
                "e": msg}
        return render_template('error_page.jinja2', pcfg=pcfg), 403

    @app.errorhandler(410)
    def err_gone(msg):
        pcfg = {"title": gettext("Whoops, something failed."),
                "error": 410, "message": gettext("Gone"),
                "e": msg}
        return render_template('error_page.jinja2', pcfg=pcfg), 410

    if not app.debug:
        @app.errorhandler(500)
        def err_failed(msg):
            pcfg = {"title": gettext("Whoops, something failed."),
                    "error": 500,
                    "message": gettext("Something is broken"),
                    "e": msg}
            return render_template('error_page.jinja2', pcfg=pcfg), 500

    # Other commands
    @app.cli.command()
    def routes():
        """Dump all routes of defined app"""
        table = texttable.Texttable()
        table.set_deco(texttable.Texttable().HEADER)
        table.set_cols_dtype(['t', 't', 't'])
        table.set_cols_align(["l", "l", "l"])
        table.set_cols_width([50, 30, 80])

        table.add_rows([["Prefix", "Verb", "URI Pattern"]])

        for rule in sorted(app.url_map.iter_rules(), key=lambda x: str(x)):
            methods = ','.join(rule.methods)
            table.add_row([rule.endpoint, methods, rule])

        print(table.draw())

    @app.cli.command()
    def config():
        """Dump config"""
        pp(app.config)

    @app.cli.command()
    def seed():
        """Seed database with default content"""
        make_db_seed(db)

    @app.cli.command()
    def createuser():
        """Create an user"""
        username = click.prompt("Username", type=str)
        email = click.prompt("Email", type=str)
        password = click.prompt("Password",
                                type=str,
                                hide_input=True,
                                confirmation_prompt=True)
        while True:
            role = click.prompt("Role [admin/user]", type=str)
            if role == "admin" or role == "user":
                break

        if click.confirm('Do you want to continue ?'):
            role = Role.query.filter(Role.name == role).first()
            if not role:
                raise click.UsageError('Roles not present in database')
            u = user_datastore.create_user(
                name=username,
                email=email,
                password=encrypt_password(password),
                roles=[role]
            )

            actor = create_actor(u)
            actor.user = u
            actor.user_id = u.id
            db.session.add(actor)

            db.session.commit()

            if FSConfirmable.requires_confirmation(u):
                FSConfirmable.send_confirmation_instructions(u)
                print("Look at your emails for validation instructions.")
    return app
