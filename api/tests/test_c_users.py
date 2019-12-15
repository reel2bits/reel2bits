from helpers import login, logout, register
import json


def test_empty_db(client, session):
    """Start with a blank database."""

    rv = client.get("/home")
    assert rv.status_code == 200


# TODO FIXME oauth
def test_login_logout(client, session):
    """Make sure login and logout works."""

    resp = register(client, "dashie@sigpipe.me", "fluttershy", "UserA", "User A")
    assert resp.status_code == 200

    resp = json.loads(resp.data)
    assert "created_at" in resp
    assert "access_token" in resp

    rv = login(client, "dashie@sigpipe.me", "fluttershy")
    rv = client.get("/home")
    assert rv.status_code == 200
    assert b"Logged as UserA" in rv.data

    rv = logout(client)
    rv = client.get("/home")
    assert rv.status_code == 200
    assert b"UserA" not in rv.data

    rv = login(client, "dashie@sigpipe.me" + "x", "fluttershy")
    assert rv.status_code == 200
    assert b"Specified user does not exist" in rv.data

    rv = login(client, "dashie@sigpipe.me", "fluttershy" + "x")
    assert rv.status_code == 200
    assert b"Invalid password" in rv.data


def test_register_two_identical_users(client, session):
    # Will register
    resp = register(client, "dashie+imunique@sigpipe.me", "fluttershy", "ImUnique", "I am unique")
    assert resp.status_code == 200

    resp = json.loads(resp.data)
    assert "created_at" in resp
    assert "access_token" in resp

    # Try to register another identical
    resp = register(client, "dashie+imunique@sigpipe.me", "fluttershy", "ImUnique", "I am unique")
    assert resp.status_code == 400

    resp = json.loads(resp.data)
    # should have an error
    assert "error" in resp
    assert "ap_id" in resp["error"]


def test_register_invalid_username(client, session):
    # valid
    resp = register(client, "dashie+lasagna@sigpipe.me", "lasagnas", "garfield", "I am lasagna")
    assert resp.status_code == 200

    resp = json.loads(resp.data)
    assert "created_at" in resp
    assert "access_token" in resp

    # Invalid 1
    resp = register(client, "dashie+bigpotat@sigpipe.me", "big_potat", "ImUnique", "I am unique")
    assert resp.status_code == 400

    resp = json.loads(resp.data)
    # should have an error
    assert "error" in resp
    assert "ap_id" in resp["error"]

    # Invalid 2
    resp = register(client, "dashie+toto@sigpipe.me", "to-to", "ImUnique", "I am unique")
    assert resp.status_code == 400

    resp = json.loads(resp.data)
    # should have an error
    assert "error" in resp
    assert "ap_id" in resp["error"]


# TODO FIXME oauth
def test_change_password(client, session):
    init_password = "fluttershy"
    new_password = "jortsjortsjorts"

    resp = register(client, "dashie+UserB@sigpipe.me", init_password, "UserB", "User B")
    assert resp.status_code == 200

    resp = json.loads(resp.data)
    assert "created_at" in resp
    assert "access_token" in resp

    # Can login with initial password
    rv = login(client, "dashie+UserB@sigpipe.me", init_password)
    rv = client.get("/home")
    assert rv.status_code == 200
    assert b"Logged as UserB" in rv.data

    # Change password
    # no follow redirect or boom
    resp = client.post(
        "/change",
        data=dict(password=init_password, new_password=new_password, new_password_confirm=new_password),
        follow_redirects=False,
    )

    assert resp.status_code == 302

    # Logout
    logout(client)

    # Test login with new password
    resp = login(client, "dashie+UserB@sigpipe.me", new_password)
    rv = client.get("/home")
    print(resp.data)
    # assert b"Logged as UserB" in resp.data
    logout(client)

    # Test login with old password
    resp = login(client, "dashie+UserB@sigpipe.me", init_password)
    assert b"Invalid password" in resp.data
