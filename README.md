<h1 align="center">
  <img src="https://raw.githubusercontent.com/rhaamo/reel2bits/master/assets/logo/Logo@0.5x.png" alt="reel2bits logo">
  <br />
  reel2bits
</h1>

<p align="center">
  <a href="https://drone.sigpipe.me/dashie/reel2bits"><img src="https://drone.sigpipe.me/api/badges/dashie/reel2bits/status.svg" alt="Build Status"/></a>
  <a href="https://dev.sigpipe.me/dashie/reel2bits/src/branch/master/LICENSE"><img src="https://img.shields.io/badge/license-AGPL3-green.svg"/></a>
  <img src="https://img.shields.io/badge/python-%3E%3D3.6-blue.svg"/>
  <a href="https://github.com/ambv/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code Style: black" /></a>
</p>

<p align="center">
  <a href="https://sound.otter.sh/user/dashie">Example single user instance</a>
  —
  <a href="https://riot.im/app/#/room/#reel2bits:otter.sh">Matrix room: #reel2bits:otter.sh</a>
</p>

Reel2bits is a soundcloud-like self-hosted application. You can upload audio files and they get transcoded, and also compile them into albums.

ActivityPub federation is still a work in progress, everything else works.

## Versions requirement
 - Python >= 3.6 (all under 3.6 are not supported)

## Installation
    Install PostgreSQL first for the database. MySQL or SQLITE3 are unsupported as we use PostgreSQL specific extensions.
    Makes sure that encoding is/will be in UNICODE/UTF-8
    git clone http://dev.sigpipe.me/dashie/reel2bits
    cd reel2bits
    pip3 install --requirement requirements.txt
    python3 setup.py install
    # Install Pydub dependencies: https://github.com/jiaaro/pydub#dependencies
    cp config.py.sample config.py
    $EDITOR config.py
    export FLASK_ENV=<development or production>
    $ create your postgresql database, like 'reel2bits'
    $ with the postgresql shell, run using superuser on the reel2bits database:
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    flask db upgrade
    flask seed
    flask run
    Don't forget to update default Config by getting to "Your user" (top right) then "Config"

    Also install this tool : https://github.com/bbc/audiowaveform
    And adapt the path to it in config.py

## Creating an user

If you have enabled registration in config, the first user registered will be ADMIN !

Or if you have disabled registration, use the ``` flask createuser ``` command to create an user.

## Production running

    sudo easy_install3 virtualenv
    sudo su - reel2bits
    cd reel2bits
    
    >> install -> git part
    
    virtualenv -p /usr/bin/python3 venv
    or if python 3.6 from github repo:
    virtualenv -ppython3.6 venv
    
    source venv/bin/activate
    >> get back to install part
    
    pip install waitress
    
    # If you want SENTRY support (also add related things in config)
    pip install sentry-sdk[flask]
    
    
Copy systemd services files ```docs/reel2bits-*.service``` to ```/etc/systemd/system/``` and adapt them to your setup.

    systemctl enable reel2bits-web reel2bits-worker
    systemctl start reel2bits-web reel2bits-worker
    
Use ```docs/reel2bits.nginx``` as vhost template for ```X-Accel-Redirect``` part.

## Docker

TODO

## Default config
 - App Name: My reel2bits instance

## Workers
  Run the workers using:
  
    $ celery worker -A tasks.celery --loglevel=error
       
## Licensing
 - AGPL v3
 
## Others projects inspired from
 - https://github.com/tsileo/microblog.pub from Little-Boxes
 - https://funkwhale.audio
