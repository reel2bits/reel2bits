"""Un-nullify name and email of User table

Revision ID: 68a5afdc49bd
Revises: a3ada8658a05
Create Date: 2019-09-07 09:23:32.945393

"""

# revision identifiers, used by Alembic.
revision = "68a5afdc49bd"
down_revision = "a3ada8658a05"

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade():
    op.alter_column("user", "email", existing_type=sa.VARCHAR(length=255), nullable=True)
    op.drop_constraint("user_name_key", "user", type_="unique")
    op.alter_column("user", "password", existing_type=sa.VARCHAR(length=255), nullable=True)


def downgrade():
    op.create_unique_constraint("user_name_key", "user", ["name"])
    op.alter_column("user", "email", existing_type=sa.VARCHAR(length=255), nullable=False)
    op.alter_column("user", "password", existing_type=sa.VARCHAR(length=255), nullable=False)
