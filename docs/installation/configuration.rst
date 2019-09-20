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

+-------------------------+---------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
|           Key           |      Environment key      |                   Default value                    |                                Description                                |
+=========================+===========================+====================================================+===========================================================================+
| TESTING                 | APP_TESTING               | False                                              | Used only for unit tests                                                  |
+-------------------------+---------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| DEBUG                   | APP_DEBUG                 | False                                              | Used in development mode                                                  |
+-------------------------+---------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| WTF_CSRF_ENABLED        | APP_WTF_CSRF              | True                                               | Enable or disable CSRF form verification                                  |
+-------------------------+---------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| REGISTRATION_ENABLED    | APP_REGISTRATION          | True                                               | Allow user registration                                                   |
+-------------------------+---------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| SECRET_KEY              | APP_SECRET_KEY            | None                                               | Used for various security things in Flask                                 |
+-------------------------+---------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| SECURITY_PASSWORD_SALT  | APP_SEC_PASS_SALT         | None                                               | Used for salting the users passwords                                      |
+-------------------------+---------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| SQLALCHEMY_DATABASE_URI | APP_DB_URI                | postgresql+psycopg2://postgres@localhost/reel2bits | Database connection chain                                                 |
+-------------------------+---------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| SQLALCHEMY_ECHO         | APP_DB_ECHO               | False                                              | Do SQLAlchemy needs to echo every queries, useful in dev/debug            |
+-------------------------+---------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| SECURITY_CONFIRMABLE    | APP_SEC_CONFIRMABLE       | True                                               | Should users have to confirm their email address                          |
+-------------------------+---------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| BABEL_DEFAULT_LOCALE    | APP_API_DEFAULT_LOCALE    | en                                                 | Backend default locale                                                    |
+-------------------------+---------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| BABEL_DEFAULT_TIMEZONE  | APP_API_DEFAULT_TIMEZONE  | UTC                                                | Backend default timezone, might have no effect                            |
+-------------------------+---------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| AUDIOWAVEFORM_BIN       | APP_AUDIOWAVEFORM_BIN     | /usr/local/bin/audiowaveform                       | Path to the Audiowaveform tool                                            |
+-------------------------+---------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| SENTRY_DSN              | APP_SENTRY_DSN            | None                                               | If you use sentry you can define your DSN here                            |
+-------------------------+---------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| CELERY_BROKER_URL       | APP_CELERY_BROKER_URL     | redis://127.0.0.1:6379/0                           | Ideally the same as the following                                         |
+-------------------------+---------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| CELERY_RESULT_BACKEND   | APP_CELERY_RESULT_BACKEND | redis://127.0.0.1:6379/0                           |                                                                           |
+-------------------------+---------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| AP_DOMAIN               | APP_AP_DOMAIN             | localhost                                          | The domain you uses for your instance, needed even if AP_ENABLED is False |
+-------------------------+---------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| AP_ENABLED              | APP_AP_ENABLED            | False                                              | Is the ActivityPub backend active                                         |
+-------------------------+---------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| SOURCES_REPOSITORY_URL  | APP_SRCS_REPO_URL         | Url to the source code                             | You should set your own repo url if you have done any customisation       |
+-------------------------+---------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| MAIL_SERVER             | APP_MAIL_SERVER           | localhost                                          | Mail server IP or DNS                                                     |
+-------------------------+---------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| MAIL_PORT               | APP_MAIL_PORT             | 25                                                 | Mail server port                                                          |
+-------------------------+---------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| MAIL_USE_TLS            | APP_MAIL_USE_TLS          | False                                              | Mail server is using TLS ?                                                |
+-------------------------+---------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| MAIL_USE_SSL            | APP_MAIL_USE_SSL          | False                                              | Mail server is using SSL ?                                                |
+-------------------------+---------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| MAIL_USERNAME           | APP_MAIL_USERNAME         | None                                               | Mail server username                                                      |
+-------------------------+---------------------------+----------------------------------------------------+---------------------------------------------------------------------------+
| MAIL_PASSWORD           | APP_MAIL_PASSWORD         | None                                               | Mail server password                                                      |
+-------------------------+---------------------------+----------------------------------------------------+---------------------------------------------------------------------------+

Upload paths
------------

You can use the following keys to define upload paths:

- UPLOADS_DEFAULT_DEST, default: /home/reel2bits/uploads
- UPLOADED_SOUNDS_DEST, default: /home/reel2bits/uploads/sounds
- UPLOADED_WAVEFORMS_DEST, default: /home/reel2bits/uploads/sounds

Paths of sounds and waveforms should be under the default one.
