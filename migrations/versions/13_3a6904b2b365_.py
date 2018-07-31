"""Add user locale

Revision ID: 3a6904b2b365
Revises: eb934854f591
Create Date: 2017-01-01 15:00:38.605336

"""

# revision identifiers, used by Alembic.
revision = '3a6904b2b365'
down_revision = 'eb934854f591'

import sqlalchemy as sa  # noqa: E402
from alembic import op  # noqa: E402


def upgrade():
    op.add_column('user', sa.Column('locale', sa.String(length=5),
                                    nullable=True))


def downgrade():
    op.drop_column('user', 'locale')
