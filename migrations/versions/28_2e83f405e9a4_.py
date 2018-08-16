"""Add Activity and Follower

Revision ID: 2e83f405e9a4
Revises: 687d40646d63
Create Date: 2018-08-06 16:42:14.355373

"""

# revision identifiers, used by Alembic.
revision = "2e83f405e9a4"
down_revision = "687d40646d63"

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402
from sqlalchemy.dialects import postgresql  # noqa: E402
import sqlalchemy_utils  # noqa: E402


def upgrade():
    op.create_table(
        "activity",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor", sa.Integer(), nullable=True),
        sa.Column("uuid", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=True),
        sa.Column("url", sqlalchemy_utils.types.url.URLType(), nullable=True),
        sa.Column("type", sa.String(length=100), nullable=True),
        sa.Column("payload", sqlalchemy_utils.types.json.JSONType(), nullable=True),
        sa.Column("creation_date", sa.DateTime(), nullable=True),
        sa.Column("delivered", sa.Boolean(), nullable=True),
        sa.Column("delivered_date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["actor"], ["actor.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
        sa.UniqueConstraint("uuid"),
    )
    op.create_index(op.f("ix_activity_type"), "activity", ["type"], unique=False)
    op.create_table(
        "followers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=True),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.Column("creation_date", sa.DateTime(), nullable=True),
        sa.Column("modification_date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["actor_id"], ["actor.id"]),
        sa.ForeignKeyConstraint(["target_id"], ["actor.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("actor_id", "target_id", name="unique_following"),
        sa.UniqueConstraint("uuid"),
    )
    op.drop_table("follow")


def downgrade():
    op.create_table(
        "follow",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column(
            "uuid", postgresql.UUID(), server_default=sa.text("uuid_generate_v4()"), autoincrement=False, nullable=True
        ),
        sa.Column("creation_date", postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.Column("modification_date", postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint("id", name="follow_pkey"),
        sa.UniqueConstraint("uuid", name="follow_uuid_key"),
    )
    op.drop_table("followers")
    op.drop_index(op.f("ix_activity_type"), table_name="activity")
    op.drop_table("activity")
