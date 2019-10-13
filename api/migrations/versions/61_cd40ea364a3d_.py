"""Add annoucement column in config

Revision ID: cd40ea364a3d
Revises: 81374a1dedde
Create Date: 2019-10-13 07:57:16.932169

"""

# revision identifiers, used by Alembic.
revision = "cd40ea364a3d"
down_revision = "81374a1dedde"

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade():
    op.add_column("config", sa.Column("announcement", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("config", "announcement")
