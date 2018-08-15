"""UserLogging now use an item_id instead of hardcoded sound_id

Revision ID: 2ec399782f52
Revises: 835be4f73770
Create Date: 2018-08-01 10:36:44.943241

"""

# revision identifiers, used by Alembic.
revision = "2ec399782f52"
down_revision = "835be4f73770"

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade():
    op.add_column("user_logging", sa.Column("item_id", sa.Integer(), nullable=True))
    op.drop_constraint("user_logging_sound_id_fkey", "user_logging", type_="foreignkey")
    op.drop_column("user_logging", "sound_id")


def downgrade():
    op.add_column(
        "user_logging",
        sa.Column("sound_id", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.create_foreign_key(
        "user_logging_sound_id_fkey", "user_logging", "sound", ["sound_id"], ["id"]
    )
    op.drop_column("user_logging", "item_id")
