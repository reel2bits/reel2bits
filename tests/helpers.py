import json
from os.path import join, dirname
from jsonschema import validate


# TODO FIXME oauth
def login(client, email, password):
    return client.post("/login", data=dict(email=email, password=password), follow_redirects=True)


# TODO FIXME oauth
def logout(client):
    return client.get("/logout", follow_redirects=True)


# TODO FIXME oauth
def register(c, email, password, name):

    logout(c)
    resp = c.post(
        "/register",
        data=dict(email=email, password=password, password_confirm=password, name=name),
        follow_redirects=True,
    )
    # should be directly logged
    resp = c.get("/home")
    assert b"Logged as" in resp.data
    # logout
    logout(c)
    resp = c.get("/home")
    assert b"Logged as" not in resp.data


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
