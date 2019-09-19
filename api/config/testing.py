from .config import BaseConfig


class Config(BaseConfig):
    DEBUG = True
    TESTING = True
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "udf298euf02uf2f02f2uf0"
    SECURITY_PASSWORD_SALT = "lolpotat"
    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://dashie@localhost:5432/reel2bits_test"

    # Bcrypt algorithm hashing rounds (reduced for testing purposes only!)
    BCRYPT_LOG_ROUNDS = 4

    AP_DOMAIN = "localhost.localdomain"
    AP_ENABLED = True
