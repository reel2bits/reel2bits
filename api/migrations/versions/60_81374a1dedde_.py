"""Add artwork for album and track and user avatar

Revision ID: 81374a1dedde
Revises: d0d03eeb0713
Create Date: 2019-10-09 09:14:48.485486

"""

# revision identifiers, used by Alembic.
revision = "81374a1dedde"
down_revision = "d0d03eeb0713"

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade():
    op.add_column("album", sa.Column("artwork_filename", sa.String(length=255), nullable=True))
    op.add_column("sound", sa.Column("artwork_filename", sa.String(length=255), nullable=True))
    op.add_column("user", sa.Column("avatar_filename", sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column("user", "avatar_filename")
    op.drop_column("sound", "artwork_filename")
    op.drop_column("album", "artwork_filename")
