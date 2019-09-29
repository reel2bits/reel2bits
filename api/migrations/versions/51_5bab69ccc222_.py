"""Add fields for file and transcode size

Revision ID: 5bab69ccc222
Revises: d1bd23cce08f
Create Date: 2019-09-29 16:10:42.433751

"""

# revision identifiers, used by Alembic.
revision = "5bab69ccc222"
down_revision = "d1bd23cce08f"

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade():
    op.add_column("sound", sa.Column("file_size", sa.Integer(), nullable=True))
    op.add_column("sound", sa.Column("transcode_file_size", sa.Integer(), nullable=True))


def downgrade():
    op.drop_column("sound", "transcode_file_size")
    op.drop_column("sound", "file_size")
