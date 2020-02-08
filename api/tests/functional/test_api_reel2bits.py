from helpers import headers, login, register, bearerhdr
from models import User

"""
controllers/api/reel2bits.py
"""


def test_licenses(client, session):
    """
    GET /api/reel2bits/licenses
    """
    resp = client.get("/api/reel2bits/licenses", headers=headers())
    assert resp.status_code == 200
    assert isinstance(resp.json, list)
    assert len(resp.json) > 4


def test_genres(client, session):
    """
    GET /api/reel2bits/genres
    """
    resp = client.get("/api/reel2bits/genres", headers=headers())
    assert resp.status_code == 200
    assert isinstance(resp.json, list)


# TODO genres filtering query


def test_tags(client, session):
    """
    GET /api/reel2bits/tags
    """
    resp = client.get("/api/reel2bits/tags", headers=headers())
    assert resp.status_code == 200
    assert isinstance(resp.json, list)


# TODO tags filtering query


def test_change_password_wrong_bearer(client, session):
    """
    GET /api/reel2bits/change_password
    """
    datas = {
        "password": "testuserchangepass",
        "new_password": "owonoticeyourpassword",
        "new_password_confirmation": "owonoticeyourpassword",
    }
    resp = client.post("/api/reel2bits/change_password", data=datas, headers=bearerhdr("uwuuwu"))
    assert resp.status_code == 401, resp.data
    assert resp.json.get("error", None) == "invalid_token"


def test_change_password_doesnt_match(client, session):
    """
    GET /api/reel2bits/change_password
    """
    # Register user
    resp = register(
        client,
        "testuserchangepassnm@reel2bits.org",
        "testuserchangepassnm",
        "testuserchangepassnm",
        "test user changepass nomatch",
    )
    assert resp.status_code == 200

    # try to login
    client_id, client_secret, access_token = login(client, "testuserchangepassnm", "testuserchangepassnm")

    datas = {"password": "testuserchangepassnm", "new_password": "uwu", "new_password_confirmation": "owo"}
    resp = client.post("/api/reel2bits/change_password", data=datas, headers=bearerhdr(access_token))
    assert resp.status_code == 400, resp.data
    assert "error" in resp.json


def test_change_password_empties(client, session):
    """
    GET /api/reel2bits/change_password
    """
    # Register user
    resp = register(
        client,
        "testuserchangepassempty@reel2bits.org",
        "testuserchangepassempty",
        "testuserchangepassempty",
        "test user changepass empty",
    )
    assert resp.status_code == 200

    # try to login
    client_id, client_secret, access_token = login(client, "testuserchangepassempty", "testuserchangepassempty")

    # empty1
    datas = {"password": "", "new_password": "uwu", "new_password_confirmation": "owo"}
    resp = client.post("/api/reel2bits/change_password", data=datas, headers=bearerhdr(access_token))
    assert resp.status_code == 400, resp.data
    assert "error" in resp.json, resp.data

    # empty2
    datas = {"password": "uwu", "new_password": "", "new_password_confirmation": "owo"}
    resp = client.post("/api/reel2bits/change_password", data=datas, headers=bearerhdr(access_token))
    assert resp.status_code == 400, resp.data
    assert "error" in resp.json, resp.data

    # empty2
    datas = {"password": "uwu", "new_password": "owo", "new_password_confirmation": ""}
    resp = client.post("/api/reel2bits/change_password", data=datas, headers=bearerhdr(access_token))
    assert resp.status_code == 400, resp.data
    assert "error" in resp.json, resp.data


def test_change_password(client, session):
    """
    GET /api/reel2bits/change_password
    """
    # Register user
    resp = register(
        client, "testuserchangepass@reel2bits.org", "testuserchangepass", "testuserchangepass", "test user changepass"
    )
    assert resp.status_code == 200

    # try to login
    client_id, client_secret, access_token = login(client, "testuserchangepass", "testuserchangepass")

    print(User.query.filter(User.name == "testuserchangepass").first().password)

    # Change password
    datas = {
        "password": "testuserchangepass",
        "new_password": "owonoticeyourpassword",
        "new_password_confirmation": "owonoticeyourpassword",
    }
    resp = client.post("/api/reel2bits/change_password", data=datas, headers=bearerhdr(access_token))
    print(resp.data)
    assert resp.status_code == 200
    assert "error" not in resp.json
    assert resp.json.get("status", None) == "success"

    print(User.query.filter(User.name == "testuserchangepass").first().password)

    # Try new password
    _, _, _ = login(client, "testuserchangepass", "owonoticeyourpassword")

    # Try old login
    client_id, client_secret, access_token = login(client, "testuserchangepass", "testuserchangepass", should_fail=True)
    assert not client_id
    assert not client_secret
    assert not access_token
