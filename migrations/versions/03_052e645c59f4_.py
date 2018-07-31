"""Add updated to sounds

Revision ID: 052e645c59f4
Revises: 6b5a95742bb4
Create Date: 2016-12-31 18:19:50.261931

"""

# revision identifiers, used by Alembic.
revision = '052e645c59f4'
down_revision = '6b5a95742bb4'

import sqlalchemy as sa  # noqa: E402
from alembic import op  # noqa: E402


def upgrade():
    op.add_column('sound', sa.Column('updated', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('sound', 'updated')
