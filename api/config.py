DEBUG = True
TESTING = False
TEMPLATES_AUTO_RELOAD = DEBUG

WTF_CSRF_ENABLED = False

REGISTRATION_ENABLED = True

SECRET_KEY = "38rufm3q8uft38gjqh-g31g3j0"
SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://dashie@localhost/reel2bits"
# SQLALCHEMY_DATABASE_URI = 'sqlite:///ahrl.db'
# SQLALCHEMY_DATABASE_URI = 'mysql://dashie:saucisse@localhost/ahrl'
SQLALCHEMY_ECHO = False
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_RECORD_QUERIES = True

SECURITY_CONFIRMABLE = False
SECURITY_REGISTERABLE = True  # deactivate registration
SECURITY_RECOVERABLE = True
SECURITY_TRACKABLE = False
SECURITY_CHANGEABLE = True
SECURITY_PASSWORD_HASH = "bcrypt"
SECURITY_PASSWORD_SALT = "omgponies"
# SECURITY_URL_PREFIX = '/sec'

SECURITY_SEND_REGISTER_EMAIL = False
SECURITY_SEND_PASSWORD_CHANGE_EMAIL = False
SECURITY_SEND_PASSWORD_RESET_NOTICE_EMAIL = False

BOOTSTRAP_USE_MINIFIED = True
BOOTSTRAP_SERVE_LOCAL = True
BOOTSTRAP_CDN_FORCE_SSL = True
BOOTSTRAP_QUERYSTRING_REVVING = True

DEBUG_TB_PROFILER_ENABLED = True
DEBUG_TB_INTERCEPT_REDIRECTS = False

BABEL_DEFAULT_LOCALE = "en"
BABEL_DEFAULT_TIMEZONE = "UTC"

UPLOADED_SOUNDS_DEST = "/Users/dashie/dev/reel2bits/uploads/sounds"
UPLOADS_DEFAULT_DEST = "/Users/dashie/dev/reel2bits/uploads"
TEMP_DOWNLOAD_FOLDER = "/Users/dashie/dev/reel2bits/tmp"

AUDIOWAVEFORM_BIN = "/usr/local/bin/audiowaveform"

# Sentry
SENTRY_DSN = ""  # "https://a0c5bc0d11f74b58b8dfba79b44234e9@sentry.sigpipe.me/12"

# Redis configuration for broker, used for async background tasks
CELERY_BROKER_URL = "redis://127.0.0.1:6379/0"
CELERY_RESULT_BACKEND = "redis://127.0.0.1:6379/0"

# They needs to be identical
# You can't change them after setup !
AP_DOMAIN = "reel2bits.dev.lan.sigpipe.me"
SERVER_NAME = AP_DOMAIN
BASE_URL = "https://" + AP_DOMAIN
AP_ENABLED = True

SOURCES_REPOSITORY_URL = "https://github.com/rhaamo/reel2bits/"

# Mail setup
MAIL_SERVER = "192.168.10.10"
MAIL_PORT = 25
MAIL_USE_TLS = False
MAIL_USE_SSL = False
MAIL_USERNAME = None
MAIL_PASSWORD = None
MAIL_DEFAULT_SENDER = f"postmaster@{AP_DOMAIN}"

SWAGGER_UI_DOC_EXPANSION = "list"

# OAUTH2
# OAUTH2_TOKEN_EXPIRES_IN = {
#    'authorization_code': 864000,
#    'implicit': 3600,
#    'password': 864000,
#    'client_credentials': 864000
# }
# OAUTH2_REFRESH_TOKEN_GENERATOR = True

SECURITY_POST_LOGIN_VIEW = "/home"
SECURITY_POST_LOGOUT_VIEW = "/home"
