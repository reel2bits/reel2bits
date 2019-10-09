"""Add Sound genre

Revision ID: 0bac316ea064
Revises: 02912cfac79c
Create Date: 2019-10-05 16:09:07.936221

"""

# revision identifiers, used by Alembic.
revision = "0bac316ea064"
down_revision = "02912cfac79c"

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade():
    op.add_column("sound", sa.Column("genre", sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column("sound", "genre")
