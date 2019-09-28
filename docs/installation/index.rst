Installation
============

Project architecture
--------------------

The project relies on the following components and services to work:

- A web application server (Python/Flask/Waitress)
- A PostgreSQL database to store application data
- A redis server to store tasks data
- A celery worker to run asynchronous tasks (such as transcoding or ActivityPub)
- A `ntp-synced clock <https://wiki.debian.org/NTP>`_ to ensure federation is working seamlessly

.. note::

    The synced clock is needed for federation purpose, to assess
    the validity of incoming requests.

Software requirements
---------------------

A mostly up-to date OS, with a Python >= 3.6, and a reverse proxy such as Nginx.

Available installation methods
-------------------------------

Docker will soon be available to deploy a reel2bits instance.
For now you can install it on any Linux distribution.

.. toctree::
    :maxdepth: 1

    external_dependencies
    linux
    docker
    configuration
    systemd
    non_amd64_architectures

reel2bits packages are available for the following platforms:

- `YunoHost 3 <https://yunohost.org/>`_: https://github.com/YunoHost-Apps/reel2bits_ynh

Running reel2bits on the master branch
---------------------------------------

Traditional deployments are done using tagged releases. However, you may want to
benefit from the latest available changes, or to provide help detecting bugs
before they are included in actual releases.

To do that, you'll need to run your instance on the master branch,
which contains all the unreleased changes and features of the next version.

Please take into account that the master branch
may be unstable and will contain bugs that may affect the well being of your
instance. If you are comfortable with that, you need to backup at least your database
before pulling latest changes from the master branch.

Otherwise, the deployment process is similar to deploying with releases.

.. _reverse-proxy-setup:

Reverse proxy
--------------

In order to make reel2bits accessible from outside your server and to play nicely with other applications on your machine, you should configure a reverse proxy.

Nginx
^^^^^

Ensure you have a recent version of nginx on your server. On Debian-like system, you would have to run the following:

.. code-block:: bash

    sudo apt-get update
    sudo apt-get install nginx

On docker deployments, run the following commands:

.. code-block:: bash

    export REEL2BITS_VERSION="|version|"
    curl -L -o /etc/nginx/sites-available/reel2bits.template "https://github.com/reel2bits/reel2bits/raw/$REEL2BITS_VERSION/deploy/docker.proxy.template"
    curl -L -o /etc/nginx/reel2bits_proxy.conf "https://github.com/reel2bits/reel2bits/raw/$REEL2BITS_VERSION/deploy/reel2bits_proxy.conf"

.. code-block:: shell

    # create a final nginx configuration using the template based on your environment
    set -a && source /home/reel2bits/.env && set +a
    envsubst "`env | awk -F = '{printf \" $%s\", $$1}'`" \
        < /etc/nginx/sites-available/reel2bits.template \
        > /etc/nginx/sites-available/reel2bits.conf

    ln -s /etc/nginx/sites-available/reel2bits.conf /etc/nginx/sites-enabled/

On non-docker deployments, run the following commands:


.. parsed-literal::

    export REEL2BITS_VERSION="|version|"

    # download the needed files
    curl -L -o /etc/nginx/reel2bits_proxy.conf "https://github.com/reel2bits/reel2bits/raw/$REEL2BITS_VERSION/deploy/reel2bits_proxy.conf"
    curl -L -o /etc/nginx/sites-available/reel2bits.template "https://github.com/reel2bits/reel2bits/raw/$REEL2BITS_VERSION/deploy/docker.nginx.template"

.. code-block:: shell

    # create a final nginx configuration using the template based on your environment
    set -a && source /home/reel2bits/config/.env && set +a
    envsubst "`env | awk -F = '{printf \" $%s\", $$1}'`" \
        < /etc/nginx/sites-available/reel2bits.template \
        > /etc/nginx/sites-available/reel2bits.conf

    ln -s /etc/nginx/sites-available/reel2bits.conf /etc/nginx/sites-enabled/

.. note::

    The resulting file should not contain any variable such as ``${APP_AP_DOMAIN}``.
    You can check that using this command::

        grep '${' /etc/nginx/sites-available/reel2bits.conf

.. note::

    You can freely adapt the resulting file to your own needs, as we cannot
    cover every use case with a single template, especially when it's related
    to SSL configuration.

Finally, enable the resulting configuration:

.. code-block:: bash

    ln -s /etc/nginx/sites-available/reel2bits.conf /etc/nginx/sites-enabled/


HTTPS Configuration
:::::::::::::::::::

At this point you will need a SSL certificate to enable HTTPS on your server.
The default nginx configuration assumes you have those available at ``/etc/letsencrypt/live/${REEL2BITS_HOSTNAME}/``, which
is the path used by `certbot <https://certbot.eff.org/docs/>`_ when generating certificates with Let's Encrypt.

In you already have a certificate you'd like to use, simply update the nginx configuration
and replace ``ssl_certificate`` and ``ssl_certificate_key`` values with the proper paths.

If you don't have one, comment or remove the lines starting with ``ssl_certificate`` and ``ssl_certificate_key``. You can then proceed to generate
a certificate, as shown below:

.. code-block:: shell

    # install certbot with nginx support
    sudo apt install python-certbot-nginx
    # generate the certificate
    # (accept the terms of service if prompted)
    sudo certbot --nginx -d yourreel2bits.domain

This should create a valid certificate and edit the nginx configuration to use the new certificate.

Reloading
:::::::::

Check the configuration is valid with ``nginx -t`` then reload your nginx server with ``sudo systemctl reload nginx``.

About internal locations
^^^^^^^^^^^^^^^^^^^^^^^^

Music (and other static) files are never served by the app itself, but by the reverse
proxy. This is needed because a webserver is way more efficient at serving
files than a Python process.

However, we do want to ensure users have the right to access music files, and
it can't be done at the proxy's level. To tackle this issue, `we use
nginx's internal directive <http://nginx.org/en/docs/http/ngx_http_core_module.html#internal>`_.

When the API receives a request on its music serving endpoint, it will check
that the user making the request can access the file. Then, it will return an empty
response with a ``X-Accel-Redirect`` header. This header will contain the path
to the file to serve to the user, and will be picked by nginx, but never sent
back to the client.

Using this technique, we can ensure music files are covered by the authentication
and permission policy of your instance, while keeping as much as performance
as possible.
