"""Can null UserLogging.sound_id

Revision ID: 835be4f73770
Revises: abf095d9c9f3
Create Date: 2018-08-01 10:24:11.029977

"""

# revision identifiers, used by Alembic.
revision = '835be4f73770'
down_revision = 'abf095d9c9f3'

import sqlalchemy as sa  # noqa: E402
from alembic import op  # noqa: E402


def upgrade():
    op.alter_column('user_logging', 'sound_id',
                    existing_type=sa.INTEGER(),
                    nullable=True)


def downgrade():
    op.alter_column('user_logging', 'sound_id',
                    existing_type=sa.INTEGER(),
                    nullable=False)
