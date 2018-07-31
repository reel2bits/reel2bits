"""Add timeline model

Revision ID: b7bb72b21644
Revises: 127a4386b617
Create Date: 2017-01-03 08:40:35.121148

"""

# revision identifiers, used by Alembic.
revision = 'b7bb72b21644'
down_revision = '127a4386b617'

import sqlalchemy as sa  # noqa: E402
from alembic import op  # noqa: E402


def upgrade():
    op.create_table('timeline',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('timestamp', sa.DateTime(), nullable=True),
                    sa.Column('private', sa.Boolean(), nullable=True),
                    sa.Column('sound_id', sa.Integer(), nullable=False),
                    sa.Column('album_id', sa.Integer(), nullable=False),
                    sa.Column('user_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['album_id'], ['album.id'], ),
                    sa.ForeignKeyConstraint(['sound_id'], ['user.id'], ),
                    sa.ForeignKeyConstraint(['user_id'], ['sound.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )


def downgrade():
    op.drop_table('timeline')
