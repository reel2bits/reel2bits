"""Generate flake ids for objects

Revision ID: 7eb56606e9d6
Revises: a8e2274a18d3
Create Date: 2019-07-06 07:55:00.474793

"""

# revision identifiers, used by Alembic.
revision = "7eb56606e9d6"
down_revision = "a8e2274a18d3"

from models import db, Sound  # noqa: E402
from utils import gen_flakeid  # noqa: E402
from uuid import UUID  # noqa: E402


def upgrade():
    for sound in db.session.query(Sound).all():
        if not sound.flake_id:
            sound.flake_id = UUID(int=gen_flakeid())
    db.session.commit()


def downgrade():
    pass
