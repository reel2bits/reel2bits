import json
from os.path import join, dirname
from jsonschema import validate
import datetime


def create_oauth_app(c):
    resp = c.post(
        "/api/v1/apps",
        data=json.dumps(
            dict(
                client_name=f"pytest_{datetime.datetime.utcnow()}",
                redirect_uris="urn:ietf:wg:oauth:2.0:oob",
                scopes="read write follow push",
            )
        ),
        follow_redirects=False,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    assert resp.status_code == 200
    assert resp.json
    assert "client_id" in resp.json
    assert "client_secret" in resp.json
    assert "id" in resp.json
    assert "name" in resp.json
    assert "redirect_uri" in resp.json
    assert "website" in resp.json
    assert "vapid_key" in resp.json
    return resp.json["client_id"], resp.json["client_secret"]


def get_oauth_client_token(c, client_id, client_secret):
    resp = c.post(
        "/oauth/token",
        data=json.dumps(
            dict(
                client_id=client_id,
                client_secret=client_secret,
                grant_type="client_credentials",
                scope="read write follow push",
                redirect_uri="urn:ietf:wg:oauth:2.0:oob",
            )
        ),
        follow_redirects=False,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    assert resp.status_code == 200
    assert resp.json
    assert "access_token" in resp.json
    return resp.json["access_token"]


def get_oauth_client_token_with_credentials(c, client_id, client_secret, username, password):
    resp = c.post(
        "/oauth/token",
        data=json.dumps(
            dict(
                client_id=client_id,
                client_secret=client_secret,
                grant_type="password",
                scope="read write follow push",
                redirect_uri="urn:ietf:wg:oauth:2.0:oob",
                username=username,
                password=password,
            )
        ),
        follow_redirects=True,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    assert resp.status_code == 200, resp.data
    assert resp.json
    assert "access_token" in resp.json
    return resp.json["access_token"]


def headers(bearer=False):
    # Used for API calls to be authentified
    hdrs = {"Content-Type": "application/json"}
    if bearer:
        hdrs["Authorization"] = f"Bearer {bearer}"
    return hdrs


def login(c, username, password):
    # TODO: save client_id, client_secret and access_token in the session
    client_id, client_secret = create_oauth_app(c)
    access_token = get_oauth_client_token_with_credentials(c, client_id, client_secret, username, password)
    assert client_id
    assert client_secret
    assert access_token

    return client_id, client_secret, access_token


def logout(client):
    # TODO: remove client_id, client_secret and access_token from the session
    return True


def register(client, email, password, username, display_name):
    client_id, client_secret = create_oauth_app(client)
    bearer = get_oauth_client_token(client, client_id, client_secret)
    assert bearer is not None

    resp = client.post(
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
    assert resp.status_code == 200
    assert "access_token" in resp.json
    assert "token_type" in resp.json
    assert "scope" in resp.json
    assert "created_at" in resp.json
    return resp


def assert_valid_schema(data, schema_file):
    """ Checks whether the given data matches the schema """

    schema = _load_json_schema(schema_file)
    return validate(data, schema)


def _load_json_schema(filename):
    """ Loads the given schema file """

    relative_path = join("../schemas", filename)
    absolute_path = join(dirname(__file__), relative_path)

    with open(absolute_path) as schema_file:
        return json.loads(schema_file.read())
