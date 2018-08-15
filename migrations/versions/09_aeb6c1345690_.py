"""up

Revision ID: aeb6c1345690
Revises: fc50eb4e9b34
Create Date: 2017-01-01 01:11:11.549297

"""

# revision identifiers, used by Alembic.
revision = "aeb6c1345690"
down_revision = "fc50eb4e9b34"

import sqlalchemy as sa  # noqa: E402
from alembic import op  # noqa: E402


def upgrade():
    op.add_column(
        "sound_info", sa.Column("waveform_error", sa.Boolean(), nullable=True)
    )


def downgrade():
    op.drop_column("sound_info", "waveform_error")
