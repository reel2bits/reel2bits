"""never gonna

Revision ID: 13ca6565de5b
Revises: 14ecb77e9482
Create Date: 2016-12-31 21:36:19.703528

"""

# revision identifiers, used by Alembic.
revision = '13ca6565de5b'
down_revision = '14ecb77e9482'

import sqlalchemy as sa  # noqa: E402
from alembic import op  # noqa: E402


def upgrade():
    op.add_column('sound_info', sa.Column('type', sa.String(length=20),
                                          nullable=True))


def downgrade():
    op.drop_column('sound_info', 'type')
