"""Add Follow table

Revision ID: 687d40646d63
Revises: d3c41a9e2688
Create Date: 2018-08-06 08:37:53.206944

"""

# revision identifiers, used by Alembic.
revision = "687d40646d63"
down_revision = "d3c41a9e2688"

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402
from sqlalchemy.dialects import postgresql  # noqa: E402


def upgrade():
    print("This migration may fails if you don't already have the " "extension created")
    print("If you get an error about 'function uuid_generate_v4() " "does not exist'")
    print("please run 'CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";' " "from postgresql shell")
    print("with a valid superuser on your database.")
    op.create_table(
        "follow",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=True),
        sa.Column("creation_date", sa.DateTime(), nullable=True),
        sa.Column("modification_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
    )


def downgrade():
    op.drop_table("follow")
