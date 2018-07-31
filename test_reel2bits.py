import os
import tempfile
import pytest

from reel2bits import app as reel2bits
from flask_migrate import command
from models import db
from dbseed import make_db_seed
from alembic.config import Config


@pytest.fixture
def client():
    reel2bits.config['WTF_CSRF_ENABLED'] = False  # to be fixed :(
    reel2bits.config['DEBUG_TB_ENABLED'] = False
    reel2bits.config['DEBUG_TB_PANELS'] = ()

    reel2bits.config['SQLALCHEMY_DATABASE_URI'] = \
        'postgresql+psycopg2://dashie:saucisse@127.0.0.1/reel2bits_test'
    reel2bits.config['TESTING'] = True
    client = reel2bits.test_client()

    with reel2bits.app_context():
        db.app = reel2bits
        config = Config("migrations/alembic.ini")
        config.set_main_option("script_location", "migrations")
        command.upgrade(config, "head")
        make_db_seed(db)

    yield client

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

def test_empty_db(client):
    """Start with a blank database."""

    rv = client.get('/')
    assert rv.status_code == 200


def test_login_logout(client):
    """Make sure login and logout works."""

    rv = _do_login(client)
    assert b'Logged as toto' in rv.data

    rv = logout(client)
    assert b'toto' not in rv.data

    rv = login(client, 'dashie@sigpipe.me' + 'x', 'fluttershy')
    assert b'Specified user does not exist' in rv.data

    rv = login(client, 'dashie@sigpipe.me', 'fluttershy' + 'x')
    assert b'Invalid password' in rv.data
