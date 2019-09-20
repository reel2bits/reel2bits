from .development import Config as BaseConfig


class Config(BaseConfig):
    # See the Configuration documentation at:
    # https://docs-develop.reel2bits.org/installation/configuration.html
    # For all the config keys you can use

    # Please generate me with: openssl rand -hex 42
    SECRET_KEY = "38rufm3q8uft38gjqh-g31g3j0"
    # Please generate me with: openssl rand -hex 5
    SECURITY_PASSWORD_SALT = "omgponies"
    # Set your DB URI
    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://dashie@localhost/reel2bits"

    # Don't forget that SOUNDS and WAVEFORMS have to be under DEFAULT path folder
    UPLOADS_DEFAULT_DEST = "/Users/dashie/dev/reel2bits/uploads"
    UPLOADED_SOUNDS_DEST = "/Users/dashie/dev/reel2bits/uploads/sounds"
    UPLOADED_WAVEFORMS_DEST = "/Users/dashie/dev/reel2bits/uploads/waveforms"

    # Where is the audiowaveform binary located
    AUDIOWAVEFORM_BIN = "/usr/local/bin/audiowaveform"

    # If you are using Sentry, otherwise, set to None
    SENTRY_DSN = None

    # The domain name your instance will be using
    AP_DOMAIN = "reel2bits.dev.lan.sigpipe.me"
    # Is the ActivityPub backend active ?
    # Even at False, you needs to setup the AP_DOMAIN because it is used
    # by more things than just ActivityPub
    AP_ENABLED = True

    # Can the users register on your instance ?
    REGISTRATION_ENABLED = True

    # If you are using a modified instance, please set your own repository URL
    SOURCES_REPOSITORY_URL = "https://github.com/reel2bits/reel2bits"

    # Email settings
    MAIL_SERVER = "localhost"
    # MAIL_PORT = 25
    # MAIL_USE_TLS = False
    # MAIL_USE_SSL = False
    # MAIL_USERNAME = None
    # MAIL_PASSWORD = None

    # CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
    # CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
