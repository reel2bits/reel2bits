"""Add flake ID column for albums

Revision ID: 8b4238e4e1a3
Revises: 7eb56606e9d6
Create Date: 2019-07-12 18:12:09.386417

"""

# revision identifiers, used by Alembic.
from sqlalchemy.dialects import postgresql

revision = "8b4238e4e1a3"
down_revision = "7eb56606e9d6"

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade():
    op.add_column("album", sa.Column("flake_id", postgresql.UUID(as_uuid=True), nullable=True))


def downgrade():
    op.drop_column("album", "flake_id")
