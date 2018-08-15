"""Add markers for sound generation of infos

Revision ID: c517c68df56e
Revises: 96774be568e1
Create Date: 2016-12-31 19:52:36.320149

"""

# revision identifiers, used by Alembic.
revision = "c517c68df56e"
down_revision = "96774be568e1"

import sqlalchemy as sa  # noqa: E402
from alembic import op  # noqa: E402


def upgrade():
    op.add_column("sound_info", sa.Column("done_basic", sa.Boolean(), nullable=True))
    op.add_column("sound_info", sa.Column("done_waveform", sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column("sound_info", "done_waveform")
    op.drop_column("sound_info", "done_basic")
