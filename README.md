Reel2Bits
=====================

# Versions requirement
 - Python >= 3.3 (3.0, 3.1, 3.2 not supported)

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
    python3 reel2bits.py db upgrade
    python3 reel2bits.py db seed
    python3 reel2bits.py runserver # or whatever gunicorn whatever stuff
    Don't forget to update default Config by getting to "Your user" (top right) then "Config"

    Also install this tool : https://github.com/bbc/audiowaveform
    And adapt the path to it in config.py

# Gunicorn
    gunicorn -w 2 -b 127.0.0.1:8000 --error-logfile=errors.log --access-logfile=access.log --chdir=$PWD reel2bits:app

# Default config
 - App Name: My reel2bits instance

# Workers
  Run the workers using:
  
    $ dramatiq workers -Q <queue name>
    
  See also 'dramatiq --help' for all config (threads etc.) infos

  List of queues and descriptions:
  - upload_workflow : handle metadatas and transcoding after upload
  
# TODO
  - Albums
  - Tags
  - Genre
  - User picture
  - Transcode and serve FLAC as MP3 CBR (HTML5 doesn't support FLAC)
  - Transcode only for waveform OGG to MP3 CBR (audiowaveform doesn't support OGG)

# Licensing
 - MIT License
