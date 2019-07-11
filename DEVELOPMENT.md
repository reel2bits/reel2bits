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
  "target": "http://127.0.0.1:5000/"
}
```

Also comment `SERVER_NAME` and `BASE_URL` in `config.py` when in dev.

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
