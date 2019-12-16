import json
from os.path import join, dirname
from jsonschema import validate
import datetime


def create_oauth_app(c):
    resp = c.post(
        "/api/v1/apps",
        data=dict(
            client_name=f"pytest_{datetime.datetime.utcnow()}",
            redirect_uris="urn:ietf:wg:oauth:2.0:oob",
            scopes="read write follow push",
        ),
        follow_redirects=True,
    )
    resp = json.loads(resp.data)
    assert "client_id" in resp
    assert "client_secret" in resp
    return resp["client_id"], resp["client_secret"]


def get_oauth_client_token(c, client_id, client_secret):
    resp = c.post(
        "/oauth/token",
        data=dict(
            client_id=client_id,
            client_secret=client_secret,
            grant_type="client_credentials",
            scope="read write follow push",
            redirect_uri="urn:ietf:wg:oauth:2.0:oob",
        ),
    )
    resp = json.loads(resp.data)
    assert "access_token" in resp
    return resp["access_token"]


def headers(bearer):
    return {"Content-Type": "application/json", "Authorization": f"Bearer {bearer}"}


# TODO FIXME oauth
def login(client, email, password):
    # do not follow redirects because it will explodes
    return client.post("/login", data=dict(email=email, password=password), follow_redirects=False)


# TODO FIXME oauth
def logout(client):
    return client.get("/logout", follow_redirects=True)


def register(c, email, password, username, display_name):
    client_id, client_secret = create_oauth_app(c)
    bearer = get_oauth_client_token(c, client_id, client_secret)
    assert bearer is not None

    resp = c.post(
        "/api/v1/accounts",
        data=json.dumps(
            {
                "nickname": username,
                "locale": "en_US",
                "agreement": True,
                "username": username,
                "fullname": display_name,
                "email": email,
                "password": password,
                "confirm": password,
            }
        ),
        headers=headers(bearer),
    )
    return resp


def assert_valid_schema(data, schema_file):
    """ Checks whether the given data matches the schema """

    schema = _load_json_schema(schema_file)
    return validate(data, schema)


def _load_json_schema(filename):
    """ Loads the given schema file """

    relative_path = join("schemas", filename)
    absolute_path = join(dirname(__file__), relative_path)

    with open(absolute_path) as schema_file:
        return json.loads(schema_file.read())
