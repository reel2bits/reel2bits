Debian based distribution installation
======================================

.. note::

    This guide targets Debian 9 (Stretch), which is the latest Debian, or the latest ubuntu

External dependencies
---------------------

The guides will focus on installing reel2bits-specific components and
dependencies. However, reel2bits requires a
:doc:`few external dependencies <./external_dependencies>` for which
documentation is outside of this document scope.

Install system dependencies
---------------------------

On Debian-like systems, you can install them using:

.. code-block:: shell

    sudo apt-get update
    # Install dependencies
    sudo apt-get install python3-pip python3-venv git
    # reel2bits dependencies
    sudo apt install build-essential sox ffmpeg libavcodec-extra libjpeg-dev libmagic-dev libpq-dev postgresql-client python3-dev make libtag1v5 libmagic1 libffi6 libsox-dev libsox-fmt-all libtag1-dev libmagic-dev libffi-dev libgd-dev libmad0-dev libsndfile1-dev libid3tag0-dev libmediainfo-dev

Layout
------

All reel2bits-related files will be located under ``/home/reel2bits`` apart
from database files and a few configuration files. We will also have a
dedicated ``reel2bits`` user to launch the processes we need and own those files.

You are free to use different values here, just remember to adapt those in the
next steps.

.. _create-reel2bits-user:

Create the user and the directory:

.. code-block:: shell

    sudo useradd -r -s /usr/sbin/nologin -d /home/reel2bits -m reel2bits
    cd /home/reel2bits

Log in as the newly created user from now on:

.. code-block:: shell

    sudo -u reel2bits -H bash


Download latest reel2bits release
---------------------------------

Locate the latest release `from the release page <https://github.com/rhaamo/reel2bits/releases>`_ like ``v0.5``, or if you want to run the unstable ``master`` branch.

Still under your ``reel2bits`` user:

.. code-block:: shell
    
    # if release:
    git checkout -b v0.5 https://github.com/rhaamo/reel2bits/
    # Or master
    git checkout https://github.com/rhaamo/reel2bits/

Python dependencies
--------------------

Go to the project directory:

.. code-block:: shell

    cd reel2bits

To avoid collisions with other software on your system, Python dependencies
will be installed in a dedicated
`virtualenv <https://docs.python.org/3/library/venv.html>`_.

First, create the virtualenv:

.. code-block:: shell

    python3 -m venv /home/reel2bits/virtualenv

This will result in a ``virtualenv`` directory being created in
``/home/reel2bits/virtualenv``.

In the rest of this guide, we'll need to activate this environment to ensure
dependencies are installed within it, and not directly on your host system.

This is done with the following command:

.. code-block:: shell

    source /home/reel2bits/virtualenv/bin/activate

Finally, install the python dependencies:

.. code-block:: shell

    pip install wheel
    pip install waitress
    pip install -r requirements.txt

.. important::

    Further commands involving python should always be run after you activated
    the virtualenv, as described earlier, otherwise those commands will raise
    errors

Configuration file
------------------

You can now start to configure reel2bits:

.. code-block:: shell

    cp config.py.sample config.py

Then edit this file as you wishes.

Sentry
------

If you known, and use Sentry, you can install the python package:

.. code-block:: shell

    pip install sentry-sdk[flask]

And setup your DSN in ``config.py``.

Database setup
---------------

You should now be able to import the initial database structure:

.. code-block:: shell

    flask db upgrade

This will create the required tables and rows.

.. note::

    You can safely execute this command any time you want, this will only
    run unapplied migrations.

Then populate the database with default values (seeds):

.. code-block:: shell

    flask seed


Create an admin account
-----------------------

You can then create your first user account:

.. code-block:: shell

    flask createuser

.. important::

    If you don't create an user, the first one to register from the web interface will be administrator !

Systemd unit file
------------------

See :doc:`./systemd`.

Reverse proxy setup
--------------------

See :ref:`reverse-proxy <reverse-proxy-setup>`.
