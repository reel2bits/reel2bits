"""empty message

Revision ID: d0d03eeb0713
Revises: f0234d780af1
Create Date: 2019-10-08 07:31:12.509636

"""

# revision identifiers, used by Alembic.
revision = "d0d03eeb0713"
down_revision = "f0234d780af1"

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade():
    op.create_table(
        "album_tags",
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.Column("album_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["album_id"], ["album.id"]),
        sa.ForeignKeyConstraint(["tag_id"], ["sound_tag.id"]),
        sa.PrimaryKeyConstraint("tag_id", "album_id"),
    )
    op.add_column("album", sa.Column("genre", sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column("album", "genre")
    op.drop_table("album_tags")
