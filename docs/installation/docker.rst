Docker installation
===================

Docker is the easiest way to get a reel2bits instance up and running.

We support one type of Docker deployments:

- :ref:`Multi-container <docker-multi-container>`: each process lives in a dedicated container. This setup is more involved but also more flexible and scalable.

.. note::

    We do not distribute Docker images for non-amd64 architectures yet. However, :doc:`you can easily build
    those images yourself following our instructions <non_amd64_architectures>`, and come back to this installation guide once
    the build is over.

.. _docker-multi-container:

Multi-container installation
----------------------------

First, ensure you have `Docker <https://docs.docker.com/engine/installation/>`_ and `docker-compose <https://docs.docker.com/compose/install/>`_ installed.

Export the `version you want <https://hub.docker.com/r/reel2bits/reel2bits/tags>`_ to deploy (e.g., ``0.6.9``):

.. parsed-literal::

    export REEL2BITS_VERSION="|version|"

Download the sample docker-compose file:

.. parsed-literal::

    mkdir /srv/reel2bits
    cd /srv/reel2bits
    mkdir nginx
    curl -L -o nginx/reel2bits.template "https://github.com/reel2bits/reel2bits/raw/$REEL2BITS_VERSION/deploy/docker.nginx.template"
    curl -L -o nginx/reel2bits_proxy.conf "https://github.com/reel2bits/reel2bits/raw/$REEL2BITS_VERSION/deploy/reel2bits_proxy.conf"
    curl -L -o docker-compose.yml "https://github.com/reel2bits/reel2bits/raw/$REEL2BITS_VERSION/deploy/docker-compose.yml"

At this point, the architecture of ``/srv/reel2bits``  should look like that:

::

    .
    ├── docker-compose.yml
    └── nginx
        ├── reel2bits_proxy.conf
        └── reel2bits.template

Create your env file:

.. parsed-literal::

    curl -L -o .env "https://github.com/reel2bits/reel2bits/raw/$REEL2BITS_VERSION/deploy/env.prod.sample"
    sed -i "s/REEL2BITS_VERSION=latest/REEL2BITS_VERSION=$REEL2BITS_VERSION/" .env
    chmod 600 .env  # reduce permissions on the .env file since it contains sensitive data
    sudo nano .env


Ensure to edit it to match your needs (this file is heavily commented), in particular ``APP_SECRET_KEY``, ``APP_SEC_PASS_SALT`` or ``AP_DOMAIN``.
You should take a look at the `configuration reference <https://docs-develop.reel2bits.org/installation/configuration.html>`_ for more detailed information regarding each setting.

Then, you should be able to pull the required images:

.. code-block:: bash

    docker-compose pull

Run the database container and the initial migrations and database seeds:

.. code-block:: bash

    docker-compose up -d postgres
    docker-compose run --rm api psql -U postgres -h postgres -w -c 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";' postgres
    docker-compose run --rm api flask db upgrade
    docker-compose run --rm api flask seed

Create your admin user:

.. code-block:: bash

    docker-compose run --rm api flask createuser

Then launch the whole thing:

.. code-block:: bash

    docker-compose up -d

Now, you just need to configure your :ref:`reverse-proxy <reverse-proxy-setup>`. Don't worry, it's quite easy.
