"""Ensure users have a slug

Revision ID: be5369fae219
Revises: 2ec399782f52
Create Date: 2018-08-01 22:49:41.221164

"""

# revision identifiers, used by Alembic.
revision = "be5369fae219"
down_revision = "2ec399782f52"

from models import db, User  # noqa: E402


def upgrade():
    for user in User.query.all():
        # no need to slugify, the user name is restricted to a-Z0-9_
        user.slug = user.name
    db.session.commit()


def downgrade():
    pass
