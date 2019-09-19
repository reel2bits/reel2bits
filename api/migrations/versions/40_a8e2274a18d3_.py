"""Add Flake ID column

Revision ID: a8e2274a18d3
Revises: 463da36c5bd5
Create Date: 2019-07-06 07:45:56.731866

"""

# revision identifiers, used by Alembic.
revision = "a8e2274a18d3"
down_revision = "463da36c5bd5"

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402
from sqlalchemy.dialects import postgresql  # noqa: E402


def upgrade():
    op.add_column("sound", sa.Column("flake_id", postgresql.UUID(as_uuid=True)))


def downgrade():
    op.drop_column("sound", "flake_id")
