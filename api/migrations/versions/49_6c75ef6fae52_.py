"""Add fields for user quotas

Revision ID: 6c75ef6fae52
Revises: 15c24b2e6402
Create Date: 2019-09-29 15:10:58.011688

"""

# revision identifiers, used by Alembic.
revision = "6c75ef6fae52"
down_revision = "15c24b2e6402"

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade():
    op.add_column("config", sa.Column("user_quota", sa.Integer(), nullable=True))
    op.add_column("user", sa.Column("quota", sa.Integer(), nullable=True))


def downgrade():
    op.drop_column("user", "quota")
    op.drop_column("config", "user_quota")
