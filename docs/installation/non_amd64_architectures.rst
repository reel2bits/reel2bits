Running reel2bits on non amd64 architectures
============================================

reel2bits should be runnable on any architecture assuming reel2bits installation dependencies are satisfied.

On non-docker deployments (e.g. when deploying on linux), this should be completely transparent.

On docker deployments, you will need to build reel2bits's image yourself, because we don't provide
pre-built multi-arch images on the Docker Hub yet. The build process itself only requires git,
Docker and is described below.

Building the Docker image (reel2bits/reel2bits)
-------------------------------------------------------------

This image is intended to be used in conjunction with our :ref:`Multi-container installation guide <docker-multi-container>`.
guide.

.. parsed-literal::

    export REEL2BITS_VERSION="|version|"

.. note::

    Replace by master for building a development branch image.

.. code-block:: shell

    cd /tmp
    git clone https://github.com/reel2bits/reel2bits.git
    cd reel2bits
    git checkout $REEL2BITS_VERSION
    cd api

    # download the pre-built front-end files
    frontend_artifacts="https://assets.reel2bits.org/front-dist-${REEL2BITS_VERSION}.zip
    curl -L -o front.zip $frontend_artifacts
    unzip front.zip
    cp -r front/dist frontend

    docker build -t reel2bits/reel2bits:$REEL2BITS_VERSION .
