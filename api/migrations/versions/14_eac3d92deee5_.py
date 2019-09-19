"""Add albums

Revision ID: eac3d92deee5
Revises: 3a6904b2b365
Create Date: 2017-01-01 17:06:38.038675

"""

# revision identifiers, used by Alembic.
revision = "eac3d92deee5"
down_revision = "3a6904b2b365"

import sqlalchemy as sa  # noqa: E402
from alembic import op  # noqa: E402


def upgrade():
    op.create_table(
        "album",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("created", sa.DateTime(), nullable=True),
        sa.Column("updated", sa.DateTime(), nullable=True),
        sa.Column("description", sa.UnicodeText(), nullable=True),
        sa.Column("private", sa.Boolean(), nullable=True),
        sa.Column("slug", sa.String(length=255), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.add_column("sound", sa.Column("album_id", sa.Integer(), nullable=True))
    op.create_foreign_key(None, "sound", "album", ["album_id"], ["id"])


def downgrade():
    op.drop_constraint(None, "sound", type_="foreignkey")
    op.drop_column("sound", "album_id")
    op.drop_table("album")
