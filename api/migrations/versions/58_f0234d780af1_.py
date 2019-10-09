"""Set Sound Tag as uniques

Revision ID: f0234d780af1
Revises: ecc1c7f83374
Create Date: 2019-10-07 15:05:55.269265

"""

# revision identifiers, used by Alembic.
revision = "f0234d780af1"
down_revision = "ecc1c7f83374"

from alembic import op  # noqa: E402


def upgrade():
    op.create_unique_constraint(None, "sound_tag", ["name"])


def downgrade():
    op.drop_constraint(None, "sound_tag", type_="unique")
