import os
import sys
import pytest
import datetime
import shutil

mypath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, mypath + "/../")
from app import create_app  # noqa: E402
from models import db as _db  # noqa: E402
from models import user_datastore, Role, User, create_actor  # noqa: E402
from commands.db_datas import make_db_seed  # noqa: E402
from flask_security.utils import hash_password  # noqa: E402


@pytest.yield_fixture(scope="session")
def app():
    _app = create_app(config_filename="config.testing.Config")
    ctx = _app.test_request_context()
    ctx.push()

    yield _app

    ctx.pop()
    tmp_dir = _app.config["TESTING_UPLOADS_TMP_DIR"]
    if tmp_dir:
        shutil.rmtree(tmp_dir)


def create_default_users(_db):
    # Create four test users, A through D, and an admin, all with an actor
    # Get an user role
    role_user = Role.query.filter(Role.name == "user").first()
    assert role_user
    # Get an admin role
    role_admin = Role.query.filter(Role.name == "admin").first()
    assert role_admin

    # Create users, all 'user'
    for i in ["testusera", "testuserb", "testuserc", "testuserd"]:
        u = user_datastore.create_user(
            name=i,
            email=f"{i}@reel2bits.org",
            display_name=f"test user {i[-1]}",
            password=hash_password(i),
            roles=[role_user],
        )
        u.confirmed_at = datetime.datetime.now()

        actor = create_actor(u)
        actor.user = u
        actor.user_id = u.id
        _db.session.add(actor)

    # create an admin user
    u = user_datastore.create_user(
        name="testuseradmin",
        email="testuseradmin@reel2bits.org",
        display_name="test user admin",
        password=hash_password("testuseradmin"),
        roles=[role_admin],
    )
    u.confirmed_at = datetime.datetime.now()

    actor = create_actor(u)
    actor.user = u
    actor.user_id = u.id
    _db.session.add(actor)

    # Commit all
    _db.session.commit()


@pytest.yield_fixture(scope="session")
def db(app):
    _db.drop_all()
    with app.app_context():
        print("CREATE DB")
        _db.engine.connect().execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
        _db.create_all()

        # Seed default datas
        make_db_seed(_db)

        create_default_users(_db)

    yield _db

    print("DROP DB")
    # magic fix, without it, drop_all() doesn't return
    # also: SADeprecationWarning: The Session.close_all() method
    # is deprecated and will be removed in a future release.
    # Please refer to session.close_all_sessions().
    # but.. exception
    _db.session.close_all()
    _db.drop_all()
    print("MEOW")


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


@pytest.yield_fixture(scope="function")
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


# Check that the provisionned users exists
# Should ran first
@pytest.mark.parametrize(
    ("username", "display_name"),
    (
        ("testusera", "test user a"),
        ("testuserb", "test user b"),
        ("testuserc", "test user c"),
        ("testuseradmin", "test user admin"),
    ),
)
def test_default_users_exists(client, session, username, display_name):
    user = User.query.filter(User.name == username).first()
    assert user.name == username
    assert user.check_password(username)
    assert user.display_name == display_name
    assert len(user.actor) == 1
    assert isinstance(user.confirmed_at, datetime.datetime)
