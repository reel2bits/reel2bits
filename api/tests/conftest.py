import os
import sys
import pytest
import random
import string
from flask_security.utils import hash_password

mypath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, mypath + "/../")
from app import create_app  # noqa: E402
from models import db as _db  # noqa: E402
from models import Role, User  # noqa: E402
from commands.db_datas import make_db_seed  # noqa: E402
from models import user_datastore  # noqa: E402


@pytest.fixture(scope="session")
def app():
    app = create_app(config_filename="config.testing.Config")
    ctx = app.app_context()
    ctx.push()

    yield app

    ctx.pop()


@pytest.fixture(scope="session")
def db(app):
    _db.drop_all()
    _db.engine.connect().execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    _db.create_all()

    make_db_seed(_db)

    yield _db

    _db.drop_all()


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
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


def test_user_slugs(client, session):
    """Mass test user slugs"""
    role = Role.query.filter(Role.name == "user").first()
    ids = []
    for count in range(50):
        suffix = "".join(random.choices(string.ascii_letters + string.digits, k=20))
        username = f"test_slug_{count}_{suffix}"
        u = user_datastore.create_user(
            name=username,
            email=f"test_slug_{count}@localhost",
            password=hash_password(f"slug_{count}"),
            roles=[role],
        )
        session.commit()
        assert u.id >= 0
        ids.append(u.id)
    # Check
    for i in ids:
        user = User.query.filter(User.id == i).first()
        assert user.slug != ""
        assert user.slug is not None
        assert len(user.slug) >= 15
