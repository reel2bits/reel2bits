from tests.helpers import login, logout, register


def test_empty_db(client, session):
    """Start with a blank database."""

    rv = client.get("/")
    assert rv.status_code == 200


def test_login_logout(client, session):
    """Make sure login and logout works."""

    register(client, "dashie@sigpipe.me", "fluttershy", "UserA")

    rv = login(client, "dashie@sigpipe.me", "fluttershy")
    assert rv.status_code == 200
    assert b"Logged as UserA" in rv.data

    rv = logout(client)
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
    register(client, "dashie+imunique@sigpipe.me", "fluttershy", "ImUnique")
    logout(client)
    # Try to register another identical
    resp = client.post(
        "/register",
        data=dict(
            email="dashie+imunique@sigpipe.me", password="fluttershy", password_confirm="fluttershy", name="ImUnique"
        ),
        follow_redirects=True,
    )
    # should error
    assert b"Logged as" not in resp.data
    assert b"dashie+imunique@sigpipe.me is already associated " b"with an account." in resp.data
    assert b"Username already taken" in resp.data
    assert resp.status_code == 200


def test_change_password(client, session):
    init_password = "fluttershy"
    new_password = "jortsjortsjorts"

    register(client, "dashie+UserB@sigpipe.me", init_password, "UserB")

    # Can login with initial password
    rv = login(client, "dashie+UserB@sigpipe.me", init_password)
    assert b"Logged as UserB" in rv.data

    # Change password
    resp = client.post(
        "/change",
        data=dict(password=init_password, new_password=new_password, new_password_confirm=new_password),
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert b"You successfully changed your password." in resp.data

    # Logout
    logout(client)

    # Test login with new password
    resp = login(client, "dashie+UserB@sigpipe.me", new_password)
    print(resp.data)
    assert b"Logged as UserB" in resp.data
    logout(client)

    # Test login with old password
    resp = login(client, "dashie+UserB@sigpipe.me", init_password)
    assert b"Invalid password" in resp.data
