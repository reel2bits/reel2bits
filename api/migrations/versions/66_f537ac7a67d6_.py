"""Add User.flake_id

Revision ID: f537ac7a67d6
Revises: 0086934960fa
Create Date: 2019-11-13 14:56:17.289671

"""

# revision identifiers, used by Alembic.
revision = "f537ac7a67d6"
down_revision = "0086934960fa"

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402
from sqlalchemy.dialects import postgresql  # noqa: E402


def upgrade():
    op.add_column("user", sa.Column("flake_id", postgresql.UUID(as_uuid=True), nullable=True))


def downgrade():
    op.drop_column("user", "flake_id")
