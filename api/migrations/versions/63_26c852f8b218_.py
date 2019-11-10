"""Activity: rename actor column to actor_id

Revision ID: 26c852f8b218
Revises: 2bfa4daedfc1
Create Date: 2019-11-10 13:29:19.500514

"""

# revision identifiers, used by Alembic.
revision = "26c852f8b218"
down_revision = "2bfa4daedfc1"

from alembic import op  # noqa: E402


def upgrade():
    op.alter_column("activity", "actor", nullable=True, new_column_name="actor_id")


def downgrade():
    op.alter_column("activity", "actor_id", nullable=True, new_column_name="actor")
