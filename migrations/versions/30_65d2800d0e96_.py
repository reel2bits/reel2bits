"""Add *box field to Activities

Revision ID: 65d2800d0e96
Revises: 4291b06c81bd
Create Date: 2018-08-07 10:17:23.234828

"""

# revision identifiers, used by Alembic.
revision = '65d2800d0e96'
down_revision = '4291b06c81bd'

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade():
    op.add_column('activity', sa.Column('box', sa.String(length=100),
                                        nullable=True))


def downgrade():
    op.drop_column('activity', 'box')
