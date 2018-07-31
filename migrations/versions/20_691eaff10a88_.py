"""Can null licence

Revision ID: 691eaff10a88
Revises: 98b863ae920c
Create Date: 2018-07-31 14:15:04.913208

"""

# revision identifiers, used by Alembic.
revision = '691eaff10a88'
down_revision = '98b863ae920c'

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade():
    op.alter_column('sound', 'licence',
                    existing_type=sa.INTEGER(),
                    nullable=True,
                    existing_server_default=sa.text('0'))


def downgrade():
    op.alter_column('sound', 'licence',
                    existing_type=sa.INTEGER(),
                    nullable=False,
                    existing_server_default=sa.text('0'))
