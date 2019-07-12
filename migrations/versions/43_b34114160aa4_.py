"""Generate flake ids for albums

Revision ID: b34114160aa4
Revises: 8b4238e4e1a3
Create Date: 2019-07-12 18:12:16.228463

"""

# revision identifiers, used by Alembic.
revision = 'b34114160aa4'
down_revision = '8b4238e4e1a3'

from models import db, Album  # noqa: E402
from flake_id import gen_flakeid  # noqa: E402
from uuid import UUID  # noqa: E40


def upgrade():
    for album in db.session.query(Album).all():
        if not album.flake_id:
            album.flake_id = UUID(int=gen_flakeid())
    db.session.commit()


def downgrade():
    pass
