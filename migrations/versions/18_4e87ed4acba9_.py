"""Add instance description

Revision ID: 4e87ed4acba9
Revises: 01e6d591fe6f
Create Date: 2018-07-31 10:06:39.651909

"""

# revision identifiers, used by Alembic.
revision = '4e87ed4acba9'
down_revision = '01e6d591fe6f'

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade():
    op.add_column('config', sa.Column('app_description', sa.Text(),
                                      nullable=True))


def downgrade():
    op.drop_column('config', 'app_description')
