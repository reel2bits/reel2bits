# reel2bits

Like Soundcloud but lighter, really lighter.

Transcode Flac and Ogg to Mp3, generate some waveforms png.

HTML5 audio player.

KISS, that's all.

## TODO

- See the TODO file

## Install

- Ubuntu/debian:

    apt install libtagc0-dev libtag1-dev libmagic-dev sox libsox-fmt-mp3 libsox-dev

- Audiowaveform
    Check the documentation on how to install at: https://github.com/bbc/audiowaveform#installation
    Don't forget to adapt the path in ```conf/app.ini``` for the audiowaveform binary.

- Checkout:

    go get -v -insecure -u dev.sigpipe.me/dashie/reel2bits

Edit config: conf/app.ini

Launch how you want the "./reel2bits web" and "./reel2bits worker"
Or use the Systemd Unit files in "conf/" directory and adapt them

## Creating an user

The first created user, either CLI or web app is automatically admin.

You can create an user from CLI with ```./reel2bits createuser``` and fill the prompts.

## Docker

There is two docker images provided actually:

- dashie/reel2bits-worker:latest
- dashie/reel2bits-web:latest

No tag/stable release yet.

Volumes/bind to use:

- /data for both images
- /app/conf/app.ini and /app/conf/logging.cfg for both, default will probably doesn't works.

No ports for worker, 4000 for web.

Worker and web needs access to redis, database, and local access to files.

## Contact, issues

- Main contact: Dashie: dashie (at) sigpipe (dot) me
- Main repository: <https://dev.sigpipe.me/dashie/reel2bits>
- Main issue tracker: <https://dev.sigpipe.me/dashie/reel2bits/issues>

## Licensing

- MIT License
