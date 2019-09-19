"""Add User.local

Revision ID: fc79fead3906
Revises: aed9b823850c
Create Date: 2019-09-06 13:17:44.846238

"""

# revision identifiers, used by Alembic.
revision = "fc79fead3906"
down_revision = "aed9b823850c"

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade():
    op.add_column("user", sa.Column("local", sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column("user", "local")
