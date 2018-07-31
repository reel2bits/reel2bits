import pytest

from reel2bits import create_app
from models import db as ddb
from dbseed import make_db_seed
from alembic.config import Config
from flask_migrate import command


@pytest.fixture(scope='session')
def flask_app(request):
    app = create_app('tests/config_test.py')
    context = app.app_context()
    context.push()
    yield app
    context.pop()


@pytest.fixture(scope='session')
def test_client(request, flask_app):
    return flask_app.test_client()


@pytest.fixture(scope='session')
def db(request):
    config = Config("migrations/alembic.ini")
    config.set_main_option("script_location", "migrations")
    command.upgrade(config, "head")
    make_db_seed(ddb)

    yield ddb

    ddb.drop_all()


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


def test_empty_db(test_client):
    """Start with a blank database."""

    rv = test_client.get('/')
    assert rv.status_code == 200


def test_login_logout(test_client):
    """Make sure login and logout works."""

    rv = _do_login(test_client)
    assert b'Logged as toto' in rv.data

    rv = logout(test_client)
    assert b'toto' not in rv.data

    rv = login(test_client, 'dashie@sigpipe.me' + 'x', 'fluttershy')
    assert b'Specified user does not exist' in rv.data

    rv = login(test_client, 'dashie@sigpipe.me', 'fluttershy' + 'x')
    assert b'Invalid password' in rv.data
