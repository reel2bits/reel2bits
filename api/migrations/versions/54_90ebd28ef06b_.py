"""Remove timeline table

Revision ID: 90ebd28ef06b
Revises: 6cd62c61bc1a
Create Date: 2019-10-02 12:51:50.465763

"""

# revision identifiers, used by Alembic.
revision = "90ebd28ef06b"
down_revision = "6cd62c61bc1a"

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402
from sqlalchemy.dialects import postgresql  # noqa: E402


def upgrade():
    op.drop_table("timeline")


def downgrade():
    op.create_table(
        "timeline",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("timestamp", postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.Column("private", sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.Column("sound_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("album_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("user_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(["album_id"], ["album.id"], name="timeline_album_id_fkey"),
        sa.ForeignKeyConstraint(["sound_id"], ["user.id"], name="timeline_sound_id_fkey"),
        sa.ForeignKeyConstraint(["user_id"], ["sound.id"], name="timeline_user_id_fkey"),
        sa.PrimaryKeyConstraint("id", name="timeline_pkey"),
    )
