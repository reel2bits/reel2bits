Systemd configuration
----------------------

.. note::

    All the command lines below should be executed as root.

Systemd offers a convenient way to manage your reel2bits instance if you're
not using docker.

We'll see how to setup systemd to properly start a reel2bits instance.

First, copy the sample files:

.. parsed-literal::

    cp /home/reel2bits/reel2bits/deploy/reel2bits.target /etc/systemd/system/reel2bits.target
    cp /home/reel2bits/reel2bits/deploy/reel2bits-web.service /etc/systemd/system/reel2bits-web.service
    cp /home/reel2bits/reel2bits/deploy/reel2bits-worker.service /etc/systemd/system/reel2bits-worker.service

You should then edit thoses files as they are using the defaults values we used in this documentation, which might not
be what you've used.

Once this is done, reload systemd:

.. code-block:: shell

    systemctl daemon-reload

And start the services:

    systemctl start reel2bits.target

To ensure all reel2bits processes are started automatically on startup, run:

.. code-block:: shell

    systemctl enable reel2bits-web
    systemctl enable reel2bits-worker

You can check the statuses of all processes at any moment:

.. code-block:: shell

    systemctl status reel2bits-\*
