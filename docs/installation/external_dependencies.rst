External dependencies
=====================

Database setup (PostgreSQL)
---------------------------

reel2bits requires a PostgreSQL database to work properly. Please refer
to the `PostgreSQL documentation <https://www.postgresql.org/download/>`_
for installation instructions specific to your os.

On Debian-like systems, you would install the database server like this:

.. code-block:: shell

    sudo apt-get install postgresql postgresql-contrib

The remaining steps are heavily inspired from `this Digital Ocean guide <https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-16-04>`_.

Open a database shell:

.. code-block:: shell

    sudo -u postgres psql

Create the project database and user:

.. code-block:: shell

    CREATE DATABASE "reel2bits"
      WITH ENCODING 'utf8';
    CREATE USER reel2bits;
    GRANT ALL PRIVILEGES ON DATABASE reel2bits TO reel2bits;

.. warning::

    It's important that you use utf-8 encoding for your database,
    otherwise you'll end up with errors and crashes later on when dealing
    with music metadata that contains non-ascii chars.

Assuming you have :ref:`created your reel2bits user <create-reel2bits-user>`,
you should now be able to open a postgresql shell:

.. code-block:: shell

    sudo -u reel2bits -H psql

Unless you give a superuser access to the database user, you should also
enable some extensions on your database server. Tose are required
for reel2bits to work properly:

.. code-block:: shell

    sudo -u postgres psql reel2bits -c 'CREATE EXTENSION "uuid-ossp";'

Cache setup (Redis)
-------------------

reel2bits also requires a cache server:

- To handle asynchronous tasks such as music transcoding or some ActivityPub tasks

On Debian-like distributions, a redis package is available, and you can
install it:

.. code-block:: shell

    sudo apt-get install redis-server

This should be enough to have your redis server set up.

audiowaveform tool
------------------

We need the `audiowaveform tool <https://github.com/bbc/audiowaveform>`_ which is used to precompute the audio waveforms used by the players.

The best way to install it is to `follow the official documentation <https://github.com/bbc/audiowaveform#installation>`_ which already mention how to install on Ubuntu or build from sources.
