"""Add relations for UserLogging

Revision ID: eb934854f591
Revises: f41ac4617ef6
Create Date: 2017-01-01 13:13:59.716097

"""

# revision identifiers, used by Alembic.
revision = "eb934854f591"
down_revision = "f41ac4617ef6"

import sqlalchemy as sa  # noqa: E402
from alembic import op  # noqa: E402


def upgrade():
    op.add_column("user_logging", sa.Column("sound_id", sa.Integer(), nullable=False))
    op.create_foreign_key(None, "user_logging", "sound", ["sound_id"], ["id"])


def downgrade():
    op.drop_constraint(None, "user_logging", type_="foreignkey")
    op.drop_column("user_logging", "sound_id")
