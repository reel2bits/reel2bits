def login(client, email, password):
    return client.post(
        '/login',
        data=dict(email=email, password=password),
        follow_redirects=True)


def logout(client):
    return client.get('/logout', follow_redirects=True)


def _do_login(client):
    return login(client, 'dashie@sigpipe.me', 'fluttershy')

# Tests now


def test_empty_db(client, session):
    """Start with a blank database."""

    rv = client.get('/')
    assert rv.status_code == 200


def test_login_logout(client, session):
    """Make sure login and logout works."""

    rv = _do_login(client)
    assert b'Logged as toto' in rv.data

    rv = logout(client)
    assert b'toto' not in rv.data

    rv = login(client, 'dashie@sigpipe.me' + 'x', 'fluttershy')
    assert b'Specified user does not exist' in rv.data

    rv = login(client, 'dashie@sigpipe.me', 'fluttershy' + 'x')
    assert b'Invalid password' in rv.data
