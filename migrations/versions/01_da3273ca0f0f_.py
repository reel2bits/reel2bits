"""Add Sound and SoundInfo

Revision ID: da3273ca0f0f
Revises: 795db5a5e99b
Create Date: 2016-12-31 14:43:11.818727

"""

# revision identifiers, used by Alembic.
revision = "da3273ca0f0f"
down_revision = "795db5a5e99b"

import sqlalchemy as sa  # noqa: E402
from alembic import op  # noqa: E402


def upgrade():
    op.create_table(
        "sound",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column(
            "uploaded", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column("description", sa.UnicodeText(), nullable=True),
        sa.Column("public", sa.Boolean(), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "sound_info",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("duration", sa.Float(), nullable=True),
        sa.Column("format", sa.String(length=255), nullable=True),
        sa.Column("rate", sa.String(length=255), nullable=True),
        sa.Column("channels", sa.Integer(), nullable=True),
        sa.Column("codec", sa.String(length=255), nullable=True),
        sa.Column("sound_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["sound_id"], ["sound.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("sound_info")
    op.drop_table("sound")
