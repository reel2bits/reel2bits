DEBUG = True
TESTING = True

# Disable CSRF tokens in the Forms (only valid for testing purposes!)
WTF_CSRF_ENABLED = False

SECRET_KEY = 'udf298euf02uf2f02f2uf0'
SQLALCHEMY_DATABASE_URI = \
    'postgresql+psycopg2://postgres@database:5432/reel2bits_test'
# SQLALCHEMY_DATABASE_URI = 'sqlite:///ahrl.db'
# SQLALCHEMY_DATABASE_URI = 'mysql://dashie:saucisse@localhost/ahrl'
SQLALCHEMY_ECHO = False
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_RECORD_QUERIES = True

SECURITY_CONFIRMABLE = False
SECURITY_REGISTERABLE = True
SECURITY_RECOVERABLE = True
SECURITY_TRACKABLE = False
SECURITY_CHANGEABLE = True
SECURITY_PASSWORD_HASH = 'bcrypt'
SECURITY_PASSWORD_SALT = 'dsadsaasd'
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

UPLOADED_SOUNDS_DEST = "/home/dashie/dev/reel2bits/uploads/sounds"
UPLOADS_DEFAULT_DEST = "/home/dashie/dev/reel2bits/uploads"
TEMP_DOWNLOAD_FOLDER = "/home/dashie/dev/reel2bits/tmp"

AUDIOWAVEFORM_BIN = "/usr/local/bin/audiowaveform"

# Sentry
SENTRY_USER_ATTRS = ['name', 'email']
SENTRY_DSN = ""

# Bcrypt algorithm hashing rounds (reduced for testing purposes only!)
BCRYPT_LOG_ROUNDS = 4

AP_DOMAIN = "localhost"
SERVER_NAME = "localhost"
