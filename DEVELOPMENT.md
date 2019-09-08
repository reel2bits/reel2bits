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

## Various tips
- Authlib doesn't handle JSON, do crimes like in `controllers/api/v1/auth.py#oauth_token()`
- Authlib revoke token wants basic auth, no idea what to give, so it doesn't works
- Authlib doesn't handle optional bearer auth, use this snippet instead of `@require_oauth(None)`:

```python
current_user = None
try:
    current_token = require_oauth.acquire_token(None)
except authlib.oauth2.rfc6749.errors.MissingAuthorizationError:
    current_token = None
if current_token:
    current_user = current_token.user
# current_user is now the actual authed user or None
```