"""Add Sound.remote_uri

Revision ID: 6acfcd91acb8
Revises: 26c852f8b218
Create Date: 2019-11-10 18:59:10.866869

"""

# revision identifiers, used by Alembic.
revision = "6acfcd91acb8"
down_revision = "26c852f8b218"

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade():
    op.add_column("sound", sa.Column("remote_uri", sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column("sound", "remote_uri")
