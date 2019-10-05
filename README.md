<h1 align="center">
  <img src="https://raw.githubusercontent.com/reel2bits/reel2bits/master/api/assets/logo/Logo@0.5x.png" alt="reel2bits logo">
  <br />
  reel2bits
</h1>

<p align="center">
  <a href="https://circleci.com/gh/reel2bits/reel2bits"><img src="https://circleci.com/gh/reel2bits/reel2bits.svg?style=svg" alt="Build Status"/></a>
  <a href="https://raw.githubusercontent.com/reel2bits/reel2bits/master/LICENSE"><img src="https://img.shields.io/badge/license-AGPL3-green.svg"/></a>
  <img src="https://img.shields.io/badge/python-%3E%3D3.6-blue.svg"/>
  <a href="https://github.com/ambv/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code Style: black" /></a>
</p>

<p align="center">
  <a href="https://demo.reel2bits.org/">Demo instance</a>
  —
  <a href="https://riot.im/app/#/room/#reel2bits:otter.sh">Matrix room: #reel2bits:otter.sh</a>
  -
  <a href="https://docs-develop.reel2bits.org">Installation & Documentation</a>
</p>

Reel2bits is a soundcloud-like self-hosted opensource web application. It allows you to upload tracks, transcode them if needed and publish podcasts or albums.

ActivityPub federation is still a work in progress, everything else works.

## Installation

The official documentation is available here: https://docs-develop.reel2bits.org/admin/index.html

## Development notes

The Developper documentation is available here: https://docs-develop.reel2bits.org/contributing.html

## Translators documentation

Refers to https://docs-develop.reel2bits.org/translators.html

## Development notes

Run the backend with:

```bash
export AUTHLIB_INSECURE_TRANSPORT=1
export FLASK_ENV=development
flask run
```

Setup the frontend with `front/config/local.json`:

```json
{
  "target": "http://127.0.0.1:5000/"
}
```

And run it with:

```bash
cd front
npm run dev
```

Then you can access the frontend on http://localhost:8081 and backend requests will be proxified properly.

## Docker

TODO

## Default config
 - App Name: My reel2bits instance
 - App description: This is a reel2bits instance

## Licensing
 - AGPL v3
 
## Others projects inspired from
 - https://github.com/tsileo/microblog.pub from Little-Boxes ActivityPub backend
 - https://funkwhale.audio
