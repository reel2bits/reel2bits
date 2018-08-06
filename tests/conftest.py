import os
import sys
import pytest
mypath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, mypath + '/../')
from app import create_app  # noqa: E402
from models import db as _db  # noqa: E402
from dbseed import make_db_seed  # noqa: E402


@pytest.yield_fixture(scope='session')
def app():
    cfg = os.getenv('CONFIGTEST', 'tests/config_test.py')
    app = create_app(cfg)
    ctx = app.app_context()
    ctx.push()

    yield app

    ctx.pop()


@pytest.yield_fixture(scope='session')
def db(app):
    _db.drop_all()
    _db.engine.connect().execute(
        "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
    _db.create_all()

    make_db_seed(_db)

    yield _db

    _db.drop_all()


@pytest.fixture(scope='session')
def client(app):
    return app.test_client()


@pytest.yield_fixture(scope='function')
def session(db):
    connection = db.engine.connect()
    transaction = connection.begin()

    options = dict(bind=connection)
    session = db.create_scoped_session(options=options)

    db.session = session

    yield session

    transaction.rollback()
    connection.close()
    session.remove()
