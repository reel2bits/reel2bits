Reel2Bits
=====================

<a href="https://drone.sigpipe.me/dashie/reel2bits"><img src="https://drone.sigpipe.me/api/badges/dashie/reel2bits/status.svg" alt="Build Status"/></a>
<a href="https://dev.sigpipe.me/dashie/reel2bits/src/branch/master/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg"/></a>
<img src="https://img.shields.io/badge/python-%3E%3D3.6-blue.svg"/>

# Versions requirement
 - Python >= 3.6 (all under 3.6 are not supported)

# Installation
    Install a BDD (mysql is supported, SQLite maybe, PostgreSQL should be)
    Makes sure that encoding is/will be in UNICODE/UTF-8
    git clone http://dev.sigpipe.me/dashie/reel2bits
    cd reel2bits
    git submodule init
    git submodule update
    pip3 install --requirement requirements.txt  # if present
    # Install Pydub dependencies: https://github.com/jiaaro/pydub#dependencies
    cp config.py.sample config.py
    $EDITOR config.py
    export FLASK_ENV=<development or production>
    flask db upgrade
    flask dbseed
    flask run
    Don't forget to update default Config by getting to "Your user" (top right) then "Config"

    Also install this tool : https://github.com/bbc/audiowaveform
    And adapt the path to it in config.py

# Creating an user

If you have enabled registration in config, the first user registered will be ADMIN !

Or if you have disabled registration, use the ``` flask createuser ``` command to create an user.

# Production running

TODO

# Docker

TODO

# Default config
 - App Name: My reel2bits instance

# Workers
  Run the workers using:
  
    $ dramatiq workers -Q <queue name>
    
  See also 'dramatiq --help' for all config (threads etc.) infos

  List of queues and descriptions:
  - upload_workflow : handle metadatas and transcoding after upload
  
# TODO
  - Transcode and serve FLAC as MP3 CBR (HTML5 doesn't support FLAC)
  - Transcode only for waveform OGG to MP3 CBR (audiowaveform doesn't support OGG)

# Licensing
 - MIT License
