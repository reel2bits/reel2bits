"""Switch from public to private key

Revision ID: f41ac4617ef6
Revises: a901f35d5686
Create Date: 2017-01-01 12:11:37.745270

"""

# revision identifiers, used by Alembic.
revision = 'f41ac4617ef6'
down_revision = 'a901f35d5686'

import sqlalchemy as sa  # noqa: E402
from alembic import op  # noqa: E402


def upgrade():
    op.add_column('sound', sa.Column('private', sa.Boolean(),
                                     nullable=True))
    op.drop_column('sound', 'public')


def downgrade():
    op.add_column('sound', sa.Column('public', sa.BOOLEAN(),
                                     autoincrement=False, nullable=False))
    op.drop_column('sound', 'private')
