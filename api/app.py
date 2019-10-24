# encoding: utf-8
import logging
import os
import subprocess
from logging.handlers import RotatingFileHandler
from flask_babelex import gettext, Babel
from flask import Flask, render_template, g, send_from_directory, jsonify, safe_join, request, flash, Response
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_migrate import Migrate
from flask_security import Security
from flask_security import signals as FlaskSecuritySignals
from flask_uploads import configure_uploads, UploadSet, AUDIO, patch_request_class
from app_oauth import config_oauth
from flask_cors import CORS, cross_origin
from cachetools import cached, TTLCache
from flasgger import Swagger
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import import_string
import requests
from utils.defaults import Reel2bitsDefaults
import commands
from utils.flake_id import FlakeId
import html
from utils.meta_tags import get_default_head_tags, get_request_head_tags
from flask_mail import Message
import click
import sys

from models import db, Config, user_datastore, create_actor
from utils.various import InvalidUsage, is_admin, add_user_log, join_url

import texttable

from pprint import pprint as pp
from little_boxes import activitypub as ap
from activitypub.backend import Reel2BitsBackend

from celery import Celery

from version import VERSION

__VERSION__ = VERSION

AVAILABLE_LOCALES = ["fr", "fr_FR", "en", "en_US", "pl"]

spa_cache = TTLCache(maxsize=100, ttl=900)

try:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration as SentryFlaskIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration as SentryCeleryIntegration

    print(" * Sentry Flask/Celery support have been loaded")
    HAS_SENTRY = True
except ImportError:
    print(" * No Sentry Flask/Celery support available")
    HAS_SENTRY = False

mail = Mail()

GIT_VERSION = ""
gitpath = os.path.join(os.getcwd(), "../.git")
if os.path.isdir(gitpath):
    GIT_VERSION = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
    if GIT_VERSION:
        GIT_VERSION = GIT_VERSION.strip().decode("UTF-8")


@cached(spa_cache)
def get_spa_html(spa_url):
    if spa_url.startswith("/") or spa_url.startswith("../"):
        print("~~~ SPA: file", spa_url)
        with open(spa_url) as f:
            return f.read()
    print("~~~ SPA: url", spa_url)
    response = requests.get(join_url(spa_url, "index.html"), verify=False)
    response.raise_for_status()
    content = response.text
    return content


def make_celery(remoulade):
    celery = Celery(remoulade.import_name, broker=remoulade.config["CELERY_BROKER_URL"])
    celery.conf.update(remoulade.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with remoulade.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery  # omnomnom


def create_app(config_filename="config.development.Config", app_name=None, register_blueprints=True):
    # App configuration
    app = Flask(app_name or __name__)
    app_settings = os.getenv("APP_SETTINGS", config_filename)
    print(f" * Loading config: '{app_settings}'")
    try:
        cfg = import_string(app_settings)()
    except ImportError:
        print(" *** Cannot import config ***")
        cfg = import_string("config.config.BaseConfig")
        print(" *** Default config loaded, expect problems ***")
    if hasattr(cfg, "post_load"):
        print(" *** Doing some magic")
        cfg.post_load()
    app.config.from_object(cfg)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    Bootstrap(app)

    app.jinja_env.add_extension("jinja2.ext.with_")
    app.jinja_env.add_extension("jinja2.ext.do")
    app.jinja_env.globals.update(is_admin=is_admin)

    if HAS_SENTRY:
        sentry_sdk.init(
            app.config["SENTRY_DSN"],
            integrations=[SentryFlaskIntegration(), SentryCeleryIntegration()],
            release=f"{VERSION} ({GIT_VERSION})",
        )
        print(" * Sentry Flask/Celery support activated")
        print(" * Sentry DSN: %s" % app.config["SENTRY_DSN"])

    if app.debug:
        app.jinja_env.auto_reload = True
        logging.basicConfig(level=logging.DEBUG)

    # Logging
    if not app.debug:
        formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s " "[in %(pathname)s:%(lineno)d]")
        file_handler = RotatingFileHandler("%s/errors_app.log" % os.getcwd(), "a", 1000000, 1)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)

    CORS(app, origins=["*"])

    if app.debug:
        logging.getLogger("flask_cors.extension").level = logging.DEBUG

    mail.init_app(app)
    migrate = Migrate(app, db)  # noqa: F841 lgtm [py/unused-local-variable]
    babel = Babel(app)  # noqa: F841
    app.babel = babel

    template = {
        "swagger": "2.0",
        "info": {"title": "reel2bits API", "description": "API instance", "version": VERSION},
        "host": app.config["AP_DOMAIN"],
        "basePath": "/",
        "schemes": ["https"],
        "securityDefinitions": {
            "OAuth2": {
                "type": "oauth2",
                "flows": {
                    "authorizationCode": {
                        "authorizationUrl": f"https://{app.config['AP_DOMAIN']}/oauth/authorize",
                        "tokenUrl": f"https://{app.config['AP_DOMAIN']}/oauth/token",
                        "scopes": {
                            "read": "Grants read access",
                            "write": "Grants write access",
                            "admin": "Grants admin operations",
                        },
                    }
                },
            }
        },
        "consumes": ["application/json", "application/jrd+json"],
        "produces": ["application/json", "application/jrd+json"],
    }

    db.init_app(app)

    # ActivityPub backend
    back = Reel2BitsBackend()
    ap.use_backend(back)

    # Oauth
    config_oauth(app)

    # Setup Flask-Security
    security = Security(app, user_datastore)  # noqa: F841 lgtm [py/unused-local-variable]

    @FlaskSecuritySignals.password_reset.connect_via(app)
    @FlaskSecuritySignals.password_changed.connect_via(app)
    def log_password_reset(sender, user):
        if not user:
            return
        add_user_log(user.id, user.id, "user", "info", "Your password has been changed !")

    @FlaskSecuritySignals.reset_password_instructions_sent.connect_via(app)
    def log_reset_password_instr(sender, user, token):
        if not user:
            return
        add_user_log(user.id, user.id, "user", "info", "Password reset instructions sent.")

    @FlaskSecuritySignals.user_registered.connect_via(app)
    def create_actor_for_registered_user(app, user, confirm_token):
        if not user:

            return
        actor = create_actor(user)
        actor.user = user
        actor.user_id = user.id
        db.session.add(actor)
        db.session.commit()

    @babel.localeselector
    def get_locale():
        # if a user is logged in, use the locale from the user settings
        identity = getattr(g, "identity", None)
        if identity is not None and identity.id:
            return identity.user.locale
        # otherwise try to guess the language from the user accept
        # header the browser transmits.  We support fr/en in this
        # example.  The best match wins.
        return request.accept_languages.best_match(AVAILABLE_LOCALES)

    @babel.timezoneselector
    def get_timezone():
        identity = getattr(g, "identity", None)
        if identity is not None and identity.id:
            return identity.user.timezone

    @app.before_request
    def before_request():
        _config = Config.query.first()
        if not _config:
            flash(gettext("Config not found"), "error")

        cfg = {
            "REEL2BITS_VERSION_VER": VERSION,
            "REEL2BITS_VERSION_GIT": GIT_VERSION,
            "app_name": _config.app_name,
            "app_description": _config.app_description,
        }
        if GIT_VERSION:
            cfg["REEL2BITS_VERSION"] = "{0}-{1}".format(VERSION, GIT_VERSION)
        else:
            cfg["REEL2BITS_VERSION"] = VERSION

        g.cfg = cfg

    @app.errorhandler(InvalidUsage)
    def handle_invalid_usage(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    # Tracks files upload set
    sounds = UploadSet("sounds", AUDIO)
    configure_uploads(app, sounds)

    # Album artwork upload set
    artworkalbums = UploadSet("artworkalbums", Reel2bitsDefaults.artwork_extensions_allowed)
    configure_uploads(app, artworkalbums)

    # Track artwork upload set
    artworksounds = UploadSet("artworksounds", Reel2bitsDefaults.artwork_extensions_allowed)
    configure_uploads(app, artworksounds)

    # User avatars
    avatars = UploadSet("avatars", Reel2bitsDefaults.avatar_extensions_allowed)
    configure_uploads(app, avatars)

    # Total max size upload for the whole app
    patch_request_class(app, app.config["UPLOAD_TRACK_MAX_SIZE"])

    app.flake_id = FlakeId()

    if register_blueprints:
        from controllers.main import bp_main

        app.register_blueprint(bp_main)

        from controllers.admin import bp_admin

        app.register_blueprint(bp_admin)

        # ActivityPub
        from controllers.api.v1.well_known import bp_wellknown

        app.register_blueprint(bp_wellknown)

        from controllers.api.v1.nodeinfo import bp_nodeinfo

        app.register_blueprint(bp_nodeinfo)

        from controllers.api.v1.ap import bp_ap

        # Feeds
        from controllers.feeds import bp_feeds

        app.register_blueprint(bp_feeds)

        # API
        app.register_blueprint(bp_ap)

        from controllers.api.v1.auth import bp_api_v1_auth

        app.register_blueprint(bp_api_v1_auth)

        from controllers.api.v1.accounts import bp_api_v1_accounts

        app.register_blueprint(bp_api_v1_accounts)

        from controllers.api.v1.timelines import bp_api_v1_timelines

        app.register_blueprint(bp_api_v1_timelines)

        from controllers.api.v1.notifications import bp_api_v1_notifications

        app.register_blueprint(bp_api_v1_notifications)

        from controllers.api.tracks import bp_api_tracks

        app.register_blueprint(bp_api_tracks)

        from controllers.api.albums import bp_api_albums

        app.register_blueprint(bp_api_albums)

        from controllers.api.account import bp_api_account

        app.register_blueprint(bp_api_account)

        from controllers.api.reel2bits import bp_api_reel2bits

        app.register_blueprint(bp_api_reel2bits)

        # Pleroma API
        from controllers.api.pleroma_admin import bp_api_pleroma_admin

        app.register_blueprint(bp_api_pleroma_admin)

        # OEmbed
        from controllers.api.oembed import bp_api_oembed

        app.register_blueprint(bp_api_oembed)

        # Iframe
        from controllers.api.embed import bp_api_embed

        app.register_blueprint(bp_api_embed)

        swagger = Swagger(app, template=template)  # noqa: F841 lgtm [py/unused-local-variable]

        # SPA catchalls for meta tags
        from controllers.spa import bp_spa

        app.register_blueprint(bp_spa)

    @app.route("/uploads/<string:thing>/<path:stuff>", methods=["GET"])
    @cross_origin(origins="*", methods=["GET", "HEAD", "OPTIONS"], expose_headers="content-length", send_wildcard=True)
    def get_uploads_stuff(thing, stuff):
        if app.testing or app.debug:
            directory = safe_join(app.config["UPLOADS_DEFAULT_DEST"], thing)
            app.logger.debug(f"serving {stuff} from {directory}")
            return send_from_directory(directory, stuff, as_attachment=True)
        else:
            app.logger.debug(f"X-Accel-Redirect serving {stuff}")
            resp = Response("")
            resp.headers["Content-Disposition"] = f"attachment; filename={stuff}"
            resp.headers["X-Accel-Redirect"] = f"/_protected/media/{thing}/{stuff}"
            resp.headers["Content-Type"] = ""  # empty it so Nginx will guess it correctly
            return resp

    def render_tags(tags):
        """
        Given a dict like {'tag': 'meta', 'hello': 'world'}
        return a html ready tag like
        <meta hello="world" />
        """
        for tag in tags:

            yield "<{tag} {attrs} />".format(
                tag=tag.pop("tag"),
                attrs=" ".join(['{}="{}"'.format(a, html.escape(str(v))) for a, v in sorted(tag.items()) if v]),
            )

    @app.errorhandler(404)
    def page_not_found(msg):
        excluded = ["/api", "/.well-known", "/feeds", "/oauth/authorize"]
        if any([request.path.startswith(m) for m in excluded]):
            return jsonify({"error": "page not found"}), 404

        html = get_spa_html(app.config["REEL2BITS_SPA_HTML"])
        head, tail = html.split("</head>", 1)

        request_tags = get_request_head_tags(request)

        default_tags = get_default_head_tags(request.path)
        unique_attributes = ["name", "property"]

        final_tags = request_tags
        skip = []

        for t in final_tags:
            for attr in unique_attributes:
                if attr in t:
                    skip.append(t[attr])
        for t in default_tags:
            existing = False
            for attr in unique_attributes:
                if t.get(attr) in skip:
                    existing = True
                    break
            if not existing:
                final_tags.append(t)

        head += "\n" + "\n".join(render_tags(final_tags)) + "\n</head>"
        return head + tail

    @app.errorhandler(403)
    def err_forbidden(msg):
        if request.path.startswith("/api/"):
            return jsonify({"error": "access forbidden"}), 403
        pcfg = {
            "title": gettext("Whoops, something failed."),
            "error": 403,
            "message": gettext("Access forbidden"),
            "e": msg,
        }
        return render_template("error_page.jinja2", pcfg=pcfg), 403

    @app.errorhandler(410)
    def err_gone(msg):
        if request.path.startswith("/api/"):
            return jsonify({"error": "gone"}), 410
        pcfg = {"title": gettext("Whoops, something failed."), "error": 410, "message": gettext("Gone"), "e": msg}
        return render_template("error_page.jinja2", pcfg=pcfg), 410

    if not app.debug:

        @app.errorhandler(500)
        def err_failed(msg):
            if request.path.startswith("/api/"):
                return jsonify({"error": "server error"}), 500
            pcfg = {
                "title": gettext("Whoops, something failed."),
                "error": 500,
                "message": gettext("Something is broken"),
                "e": msg,
            }
            return render_template("error_page.jinja2", pcfg=pcfg), 500

    @app.after_request
    def set_x_powered_by(response):
        response.headers["X-Powered-By"] = "reel2bits"
        return response

    # Other commands
    @app.cli.command()
    def routes():
        """Dump all routes of defined app"""
        table = texttable.Texttable()
        table.set_deco(texttable.Texttable().HEADER)
        table.set_cols_dtype(["t", "t", "t"])
        table.set_cols_align(["l", "l", "l"])
        table.set_cols_width([50, 30, 80])

        table.add_rows([["Prefix", "Verb", "URI Pattern"]])

        for rule in sorted(app.url_map.iter_rules(), key=lambda x: str(x)):
            methods = ",".join(rule.methods)
            table.add_row([rule.endpoint, methods, rule])

        print(table.draw())

    @app.cli.command()
    def config():
        """Dump config"""
        pp(app.config)

    @app.cli.command(name="test-email")
    @click.option("--email", prompt=True, help="Email to send the test to")
    def test_email(email):
        """
        Test email sending.
        """
        msg = Message(subject="reel2bits test email", recipients=[email], sender=app.config["MAIL_DEFAULT_SENDER"])
        msg.body = render_template("email/test_email.txt")
        msg.html = render_template("email/test_email.html")
        try:
            mail.send(msg)
        except:  # noqa: E772
            print(f"Error sending mail: {sys.exc_info()[0]}")

    app.cli.add_command(commands.db_datas)
    app.cli.add_command(commands.users)
    app.cli.add_command(commands.roles)
    app.cli.add_command(commands.tracks)

    return app
