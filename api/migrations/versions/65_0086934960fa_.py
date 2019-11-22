"""Add Sound.remote_artwork_uri

Revision ID: 0086934960fa
Revises: 6acfcd91acb8
Create Date: 2019-11-10 19:18:26.384647

"""

# revision identifiers, used by Alembic.
revision = "0086934960fa"
down_revision = "6acfcd91acb8"

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade():
    op.add_column("sound", sa.Column("remote_artwork_uri", sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column("sound", "remote_artwork_uri")
