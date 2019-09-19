"""Remove lastname and firstname fields

Revision ID: 1a68efa16d1d
Revises: 7ce00beb5b0a
Create Date: 2018-08-17 08:53:01.901910

"""

# revision identifiers, used by Alembic.
revision = "1a68efa16d1d"
down_revision = "7ce00beb5b0a"

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade():
    op.drop_column("user", "firstname")
    op.drop_column("user", "lastname")


def downgrade():
    op.add_column("user", sa.Column("lastname", sa.VARCHAR(length=32), autoincrement=False, nullable=True))
    op.add_column("user", sa.Column("firstname", sa.VARCHAR(length=32), autoincrement=False, nullable=True))
