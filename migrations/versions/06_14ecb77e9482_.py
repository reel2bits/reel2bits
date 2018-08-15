"""More infos fields

Revision ID: 14ecb77e9482
Revises: c517c68df56e
Create Date: 2016-12-31 20:53:55.649816

"""

# revision identifiers, used by Alembic.
revision = "14ecb77e9482"
down_revision = "c517c68df56e"

import sqlalchemy as sa  # noqa: E402
from alembic import op  # noqa: E402


def upgrade():
    op.add_column("sound_info", sa.Column("bitrate", sa.Integer(), nullable=True))
    op.add_column(
        "sound_info", sa.Column("bitrate_mode", sa.String(length=10), nullable=True)
    )


def downgrade():
    op.drop_column("sound_info", "bitrate_mode")
    op.drop_column("sound_info", "bitrate")
