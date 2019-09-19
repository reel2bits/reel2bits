"""Add field for order in album

Revision ID: 127a4386b617
Revises: eac3d92deee5
Create Date: 2017-01-01 23:31:19.190474

"""

# revision identifiers, used by Alembic.
revision = "127a4386b617"
down_revision = "eac3d92deee5"

import sqlalchemy as sa  # noqa: E402
from alembic import op  # noqa: E402


def upgrade():
    op.add_column("sound", sa.Column("album_order", sa.Integer(), nullable=True))


def downgrade():
    op.drop_column("sound", "album_order")
