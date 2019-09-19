"""Add Activity URL to followers relationship table

Revision ID: 7ce00beb5b0a
Revises: 65d2800d0e96
Create Date: 2018-08-15 22:55:06.091571

"""

# revision identifiers, used by Alembic.
revision = "7ce00beb5b0a"
down_revision = "65d2800d0e96"

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402
import sqlalchemy_utils  # noqa: E402


def upgrade():
    op.add_column("followers", sa.Column("activity_url", sqlalchemy_utils.types.url.URLType(), nullable=True))
    op.create_unique_constraint(None, "followers", ["activity_url"])


def downgrade():
    op.drop_constraint(None, "followers", type_="unique")
    op.drop_column("followers", "activity_url")
