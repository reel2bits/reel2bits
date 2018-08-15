"""Add local field to Activities

Revision ID: 4291b06c81bd
Revises: 2e83f405e9a4
Create Date: 2018-08-07 08:38:37.986404

"""

# revision identifiers, used by Alembic.
revision = "4291b06c81bd"
down_revision = "2e83f405e9a4"

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade():
    op.add_column("activity", sa.Column("local", sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column("activity", "local")
