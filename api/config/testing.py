from .config import BaseConfig


class Config(BaseConfig):
    DEBUG = True
    TESTING = True
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
    # Bcrypt algorithm hashing rounds (reduced for testing purposes only!)
    BCRYPT_LOG_ROUNDS = 4
    CELERY_BROKER_URL = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND = "redis://redis:6379/0"
    AP_DOMAIN = "localhost.localdomain"
    AP_ENABLED = True
