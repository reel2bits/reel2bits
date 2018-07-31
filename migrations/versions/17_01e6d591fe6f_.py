"""Add transcode fields

Revision ID: 01e6d591fe6f
Revises: b7bb72b21644
Create Date: 2017-01-03 22:11:44.663000

"""

# revision identifiers, used by Alembic.
revision = '01e6d591fe6f'
down_revision = 'b7bb72b21644'

import sqlalchemy as sa  # noqa: E402
from alembic import op  # noqa: E402


def upgrade():
    op.add_column('sound', sa.Column('filename_transcoded',
                                     sa.String(length=255), nullable=True))
    op.add_column('sound', sa.Column('transcode_needed',
                                     sa.Boolean(), nullable=True))
    op.add_column('sound', sa.Column('transcode_state',
                                     sa.Integer(), server_default="0",
                                     nullable=False))


def downgrade():
    op.drop_column('sound', 'transcode_state')
    op.drop_column('sound', 'transcode_needed')
    op.drop_column('sound', 'filename_transcoded')
