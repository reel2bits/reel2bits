"""Drop User.slug uniqueness

Revision ID: 15c24b2e6402
Revises: 68a5afdc49bd
Create Date: 2019-09-07 09:29:15.708709

"""

# revision identifiers, used by Alembic.
revision = "15c24b2e6402"
down_revision = "68a5afdc49bd"

from alembic import op  # noqa: E402


def upgrade():
    op.drop_constraint("user_slug_key", "user", type_="unique")


def downgrade():
    op.create_unique_constraint("user_slug_key", "user", ["slug"])
