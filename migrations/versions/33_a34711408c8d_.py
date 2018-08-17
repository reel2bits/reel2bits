"""Add display name

Revision ID: a34711408c8d
Revises: 1a68efa16d1d
Create Date: 2018-08-17 09:05:38.156156

"""

# revision identifiers, used by Alembic.
revision = "a34711408c8d"
down_revision = "1a68efa16d1d"

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade():
    op.add_column("user", sa.Column("display_name", sa.String(length=30), nullable=True))


def downgrade():
    op.drop_column("user", "display_name")
