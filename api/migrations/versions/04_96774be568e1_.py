"""Add waveform to sound infos

Revision ID: 96774be568e1
Revises: 052e645c59f4
Create Date: 2016-12-31 19:31:52.606598

"""

# revision identifiers, used by Alembic.
revision = "96774be568e1"
down_revision = "052e645c59f4"

import sqlalchemy as sa  # noqa: E402
from alembic import op  # noqa: E402


def upgrade():
    op.add_column("sound_info", sa.Column("waveform", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("sound_info", "waveform")
