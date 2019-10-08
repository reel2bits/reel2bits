Configuration
=============

.. _configuration-file:

Letting the app know which config use
-------------------------------------

Setting the right config file to use is done by using the environment variable `APP_SETTINGS`.

If your configuration file is `api/config/prod_secret.py` you should define your variable as:

.. code-block:: shell

    APP_SETTINGS='config.prod_secret.Config'

Overriding using environment
----------------------------

Any key can be overriden using the environment, see the configuration table for the related env key

Creating your configuration file
--------------------------------

You can use `production_secret_sample.py` as example, naming them `whatyouwant_secret.py`, the `_secret.py` will make sure git ignore it.

Configuration keys and definitions
----------------------------------

+-------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
|           Key           |                   Default value                    |                                Description                                |
+=========================+====================================================+===========================================================================+
| TESTING                 | False                                              | Used only for unit tests                                                  |
+-------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| DEBUG                   | False                                              | Used in development mode                                                  |
+-------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| REGISTRATION_ENABLED    | True                                               | Allow user registration                                                   |
+-------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| SECRET_KEY              | None                                               | Used for various security things in Flask                                 |
+-------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| SECURITY_PASSWORD_SALT  | None                                               | Used for salting the users passwords                                      |
+-------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| SQLALCHEMY_DATABASE_URI | postgresql+psycopg2://postgres@localhost/reel2bits | Database connection chain                                                 |
+-------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| SQLALCHEMY_ECHO         | False                                              | Do SQLAlchemy needs to echo every queries, useful in dev/debug            |
+-------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| SECURITY_CONFIRMABLE    | True                                               | Should users have to confirm their email address                          |
+-------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| BABEL_DEFAULT_LOCALE    | en                                                 | Backend default locale                                                    |
+-------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| BABEL_DEFAULT_TIMEZONE  | UTC                                                | Backend default timezone, might have no effect                            |
+-------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| AUDIOWAVEFORM_BIN       | /usr/local/bin/audiowaveform                       | Path to the Audiowaveform tool                                            |
+-------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| SENTRY_DSN              | None                                               | If you use sentry you can define your DSN here                            |
+-------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| CELERY_BROKER_URL       | redis://127.0.0.1:6379/0                           | Ideally the same as the following                                         |
+-------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| CELERY_RESULT_BACKEND   | redis://127.0.0.1:6379/0                           |                                                                           |
+-------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| AP_DOMAIN               | localhost                                          | The domain you uses for your instance, needed even if AP_ENABLED is False |
+-------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| AP_ENABLED              | False                                              | Is the ActivityPub backend active                                         |
+-------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| SOURCES_REPOSITORY_URL  | Url to the source code                             | You should set your own repo url if you have done any customisation       |
+-------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| MAIL_SERVER             | localhost                                          | Mail server IP or DNS                                                     |
+-------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| MAIL_PORT               | 25                                                 | Mail server port                                                          |
+-------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| MAIL_USE_TLS            | False                                              | Mail server is using TLS ?                                                |
+-------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| MAIL_USE_SSL            | False                                              | Mail server is using SSL ?                                                |
+-------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| MAIL_USERNAME           | None                                               | Mail server username                                                      |
+-------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| MAIL_PASSWORD           | None                                               | Mail server password                                                      |
+-------------------------+----------------------------------------------------+---------------------------------------------------------------------------+

Upload paths
------------

You can use the following keys to define upload paths:

- UPLOADS_DEFAULT_DEST, default: /home/reel2bits/uploads
- UPLOADED_SOUNDS_DEST, default: /home/reel2bits/uploads/sounds
- UPLOADED_ARTWORK_ALBUMS_DEST, default: /home/reel2bits/uploads/artwork_albums
- UPLOADED_ARTWORK_SOUNDS_DEST, default: /home/reel2bits/uploads/artwork_sounds

Paths of sounds and waveforms should be under the default one.
