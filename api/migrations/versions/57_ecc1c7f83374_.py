"""Add tagging relationship for Sound

Revision ID: ecc1c7f83374
Revises: 0bac316ea064
Create Date: 2019-10-07 14:58:09.900722

"""

# revision identifiers, used by Alembic.
revision = "ecc1c7f83374"
down_revision = "0bac316ea064"

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade():
    op.create_table(
        "sound_tag",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "sound_tags",
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.Column("sound_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["sound_id"], ["sound.id"]),
        sa.ForeignKeyConstraint(["tag_id"], ["sound_tag.id"]),
        sa.PrimaryKeyConstraint("tag_id", "sound_id"),
    )


def downgrade():
    op.drop_table("sound_tags")
    op.drop_table("sound_tag")
