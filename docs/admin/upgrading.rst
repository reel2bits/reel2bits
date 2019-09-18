Upgrading your reel2bits instance to a newer version
====================================================

.. note::

    Before upgrading your instance, we strongly advise you to make at last a database backup.
    Ideally, you should make a full backup, including the database and the media files.

    We're commited to make upgrade as easy and straightforward as possible,
    however, reel2bits is still in development and you'll be safer with a backup.

Non-docker setup
----------------

Upgrading the backend
^^^^^^^^^^^^^^^^^^^^^

On non-docker, upgrade involves a few more commands. We assume your setup
match what is described in :doc:`/installation/linux`:

.. important::

    Further commands involving python should always be run after you activated
    the virtualenv, as described earlier, otherwise those commands will raise
    errors

Locate the latest release `from the release page <https://github.com/reel2bits/reel2bits/releases>`_ like ``v0.6``, or if you want to run the unstable ``master`` branch.

.. parsed-literal::

    sudo -u reel2bits -H bash
    cd /home/reel2bits/reel2bits/
    # If upgrading from stable releases
    git fetch -a
    git checkout v0.6
    # Or if using master:
    git pull

    # Update dependencies
    source /home/reel2bits/virtualenv/bin/activate
    pip install -r requirements.txt

Then exit your reel2bits user and run as root:

.. parsed-literal::

    sudo systemctl stop reel2bits.target

Then apply databases migrations:

.. parsed-literal::

    sudo -u reel2bits -H bash
    cd /home/reel2bits/reel2bits/
    source /home/reel2bits/virtualenv/bin/activate
    flask db upgrade

You have to update the front-end too, see :ref:`front-installation <front-installation>`.

Exit and restart services:

.. parsed-literal::

    sudo systemctl start reel2bits.target

