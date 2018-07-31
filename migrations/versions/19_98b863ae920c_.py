"""Add licence field

Revision ID: 98b863ae920c
Revises: 4e87ed4acba9
Create Date: 2018-07-31 12:49:16.891194

"""

# revision identifiers, used by Alembic.
revision = '98b863ae920c'
down_revision = '4e87ed4acba9'

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade():
    op.add_column('sound', sa.Column('licence', sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    op.drop_column('sound', 'licence')
