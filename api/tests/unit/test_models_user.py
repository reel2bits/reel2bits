"""
This file (test_models_user.py) contains the unit tests for the models.py User model.
"""

from flask_security.utils import hash_password

from models import db, user_datastore, Role
from utils.defaults import Reel2bitsDefaults


def test_new_user(session):
    role = Role.query.filter(Role.name == "user").first()
    assert role

    u = user_datastore.create_user(
        name="test_user",
        email="test_user@reel2bits.org",
        display_name="test user",
        password=hash_password("test_user"),
        roles=[role],
    )
    db.session.commit()

    assert u
    assert u.password != u.name
    assert u.created_at
    assert u.locale == "en"
    assert u.timezone == "UTC"
    assert u.slug == u.name  # slug is not used anymore
    assert u.quota == Reel2bitsDefaults.user_quotas_default
    assert u.local
    assert role in u.roles
    assert not u.is_admin()
    assert u.username() == u.display_name
    assert u.get_user_id() == u.id
    assert u.check_password(u.name)
    assert u.acct()
    assert u.flake_id
