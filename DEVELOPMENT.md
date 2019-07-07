# Various development notes

## Backend

Use the doc in the README.md

Run server with:

```shell
export AUTHLIB_INSECURE_TRANSPORT=1
export FLASK_ENV=development
flask run
```

All ActivityPub code (inbound or outbound) needs to have the celery worker running.

## Unittests (backend)

```shell
export CONFIGTEST=configtest.py
pytest
```

## Unittests (frontend)

None yet

## Frontend

Create `front/config/local.json` with:

```json
{
  "target": "http://reel2bits.dev.lan.sigpipe.me/"
}
```

Uses whatever dns you want, but it needs to match the AP_DOMAIN in `config.py`.

Also add that dns into your `/etc/hosts`.

And you need to run it proxified by nginx or whatever else.

Run the front with: `cd front && npm run dev`

Then access to the front on: http://localhost:8081

The backend will be automatically proxified.

## Linters

Backend:

```
flake8 .
black .
```

Frontend:
```
npm run lint
```
