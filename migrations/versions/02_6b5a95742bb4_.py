"""Add Sound filename

Revision ID: 6b5a95742bb4
Revises: da3273ca0f0f
Create Date: 2016-12-31 15:24:39.095388

"""

# revision identifiers, used by Alembic.
revision = '6b5a95742bb4'
down_revision = 'da3273ca0f0f'

import sqlalchemy as sa  # noqa: E402
from alembic import op  # noqa: E402


def upgrade():
    op.add_column('sound', sa.Column('filename', sa.String(length=255),
                                     nullable=True))


def downgrade():
    op.drop_column('sound', 'filename')
