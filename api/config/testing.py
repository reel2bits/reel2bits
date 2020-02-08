from .config import BaseConfig
import tempfile
import os


class Config(BaseConfig):
    DEBUG = True
    TESTING = True
    MAIL_DEBUG = True
    WTF_CSRF_ENABLED = False
    REGISTRATION_ENABLED = True
    SECRET_KEY = "udf298euf02uf2f02f2uf0"
    SECURITY_CONFIRMABLE = False
    SECURITY_REGISTERABLE = True
    SECURITY_RECOVERABLE = True
    SECURITY_TRACKABLE = False
    SECURITY_CHANGEABLE = True
    SECURITY_PASSWORD_HASH = "bcrypt"
    SECURITY_PASSWORD_SALT = "dsadsaasd"
    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://postgres@localhost:5432/reel2bits_test"
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_SEND_PASSWORD_CHANGE_EMAIL = False
    SECURITY_SEND_PASSWORD_RESET_NOTICE_EMAIL = False
    SECURITY_SEND_PASSWORD_RESET_EMAIL = False
    # Bcrypt algorithm hashing rounds (reduced for testing purposes only!)
    BCRYPT_LOG_ROUNDS = 4
    CELERY_BROKER_URL = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND = "redis://redis:6379/0"
    REEL2BITS_HOSTNAME = "localhost.localdomain"
    SERVER_NAME = REEL2BITS_HOSTNAME
    REEL2BITS_PROTOCOL = "http"
    # AP is internally enabled, it will just not broadcast things outside
    AP_ENABLED = False
    # Uploads directories
    tmp_dir = tempfile.mkdtemp()
    TESTING_UPLOADS_TMP_DIR = tmp_dir
    UPLOADS_DEFAULT_DEST = os.path.join(tmp_dir, "uploads")
    UPLOADED_SOUNDS_DEST = os.path.join(tmp_dir, "uploads/sounds")
    UPLOADED_ARTWORKALBUMS_DEST = os.path.join(tmp_dir, "uploads/artwork_albums")
    UPLOADED_ARTWORKSOUNDS_DEST = os.path.join(tmp_dir, "uploads/artwork_sounds")
    UPLOADED_AVATARS_DEST = os.path.join(tmp_dir, "uploads/avatars")
