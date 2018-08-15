"""Finally, not nullable

Revision ID: abf095d9c9f3
Revises: 691eaff10a88
Create Date: 2018-07-31 14:23:26.425828

"""

# revision identifiers, used by Alembic.
revision = "abf095d9c9f3"
down_revision = "691eaff10a88"

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade():
    op.alter_column(
        "sound",
        "licence",
        existing_type=sa.INTEGER(),
        nullable=False,
        existing_server_default=sa.text("0"),
    )


def downgrade():
    op.alter_column(
        "sound",
        "licence",
        existing_type=sa.INTEGER(),
        nullable=True,
        existing_server_default=sa.text("0"),
    )
