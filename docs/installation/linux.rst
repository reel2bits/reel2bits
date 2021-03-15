Debian-based distribution installation
======================================

.. note::

    This guide targets Debian 9 (Stretch), which is the latest Debian. It also apply to the latest Ubuntu

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
    sudo apt-get install python3-pip python3-venv git rustc
    # reel2bits dependencies
    sudo apt install build-essential sox ffmpeg libavcodec-extra libjpeg-dev libmagic-dev libpq-dev postgresql-client python3-dev make libtag1v5 libmagic1 libffi6 libsox-dev libsox-fmt-all libtag1-dev libffi-dev libgd-dev libmad0-dev libsndfile1-dev libid3tag0-dev libmediainfo-dev

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

Locate the latest stable release `from the release page <https://github.com/rhaamo/reel2bits/releases>`_ like ``v0.5``, or if you want to run the unstable, use the ``master`` branch.

Still under your ``reel2bits`` user:

.. code-block:: shell

    # if release:
    git clone -b v0.5 https://github.com/reel2bits/reel2bits/
    # Or master
    git clone https://github.com/reel2bits/reel2bits/

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
    pip install -r api/requirements.txt

.. warning::

    Further commands involving python should always be run after you activated
    the virtualenv, as described earlier, otherwise those commands will raise
    errors

Configuration file
------------------

Please look at :ref:`the dedicated configuration page <configuration-file>`.

Sentry
------

If you know and use Sentry, you can install the python package:

.. code-block:: shell

    pip install sentry-sdk[flask]

And setup your DSN in ``config.py``.

Database setup
---------------

You should now be able to import the initial database structure:

.. code-block:: shell

    # in the 'api' folder
    flask db upgrade

This will create the required tables and rows.

.. note::

    You can safely execute this command any time you want, this will only
    run unapplied migrations.

Then populate the database with default values (seeds):

.. code-block:: shell

    # in the 'api' folder
    flask db-datas 000-seeds

Test email sending
------------------

This step is tmportant if you configured the app to have user confirm their email !

.. code-block:: bash

    flask test-email --email=EMAIL_TO_SEND_TEST_TO

Create an admin account
-----------------------

You can then create your first user account:

.. code-block:: shell

    # in the 'api' folder
    flask users create

.. warning::

    If you don't create an user, the first one to register from the web interface will be administrator !

.. _front-installation:

Front installation
------------------

You also need to either get a frontend prebuild or build it yourself.

Pre-build
^^^^^^^^^

- The URL for a stable release will be `https://assets.reel2bits.org/front-dist-master-v0.5.zip`.
- The URL for master will be `https://assets.reel2bits.org/front-dist-master.zip`.

You can always go to https://assets.reel2bits.org/ to check the available archives, and test the link before downloading it.

Get the archive and extract:

.. code-block:: shell

    sudo -u reel2bits -H bash
    cd
    wget <the URL defined earlier>
    # use the stable or master name you got earlier too
    unzip "front-dist-master-v0.5.zip" -d extract
    # beware with this command, take care
    rm -rf "reel2bits/front/dist/*"
    cp -r extract/dist/* reel2bits/front/dist/
    # same with this one
    rm -rf "extract"

.. warning::

    Any update to the frontend files needs either a restart of the `reel2bits-web` service, or wait until the file cache expires.

Build it yourself
^^^^^^^^^^^^^^^^^

Make sure you have Node.js installed then:

.. code-block:: shell

    sudo -u reel2bits -H bash
    cd reel2bits/front
    yarn
    npm run build

That's it.

Systemd unit file
------------------

See :doc:`./systemd`.

Reverse proxy setup
--------------------

See :ref:`reverse-proxy <reverse-proxy-setup>`.
