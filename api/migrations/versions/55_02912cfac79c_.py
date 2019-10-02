"""Add meta_deleted flag to Actors

Revision ID: 02912cfac79c
Revises: 90ebd28ef06b
Create Date: 2019-10-02 13:05:13.668151

"""

# revision identifiers, used by Alembic.
revision = "02912cfac79c"
down_revision = "90ebd28ef06b"

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade():
    op.add_column("actor", sa.Column("meta_deleted", sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column("actor", "meta_deleted")
