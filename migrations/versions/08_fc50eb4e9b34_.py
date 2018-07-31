"""empty message

Revision ID: fc50eb4e9b34
Revises: 13ca6565de5b
Create Date: 2016-12-31 21:41:01.810513

"""

# revision identifiers, used by Alembic.
revision = 'fc50eb4e9b34'
down_revision = '13ca6565de5b'

import sqlalchemy as sa  # noqa: E402
from alembic import op  # noqa: E402


def upgrade():
    op.add_column('sound_info', sa.Column('type_human', sa.String(length=20),
                                          nullable=True))


def downgrade():
    op.drop_column('sound_info', 'type_human')
