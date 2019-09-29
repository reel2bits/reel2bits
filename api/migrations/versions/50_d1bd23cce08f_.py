"""Add user quota count

Revision ID: d1bd23cce08f
Revises: 6c75ef6fae52
Create Date: 2019-09-29 15:20:26.364904

"""

# revision identifiers, used by Alembic.
revision = "d1bd23cce08f"
down_revision = "6c75ef6fae52"

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade():
    op.add_column("user", sa.Column("quota_count", sa.Integer(), nullable=True))


def downgrade():
    op.drop_column("user", "quota_count")
