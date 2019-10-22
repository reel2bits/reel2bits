"""Migrate quota and file sizes to bigint

Revision ID: 2bfa4daedfc1
Revises: cd40ea364a3d
Create Date: 2019-10-22 09:18:01.494953

"""

# revision identifiers, used by Alembic.
revision = "2bfa4daedfc1"
down_revision = "cd40ea364a3d"

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade():
    op.alter_column("config", "user_quota", existing_type=sa.INTEGER(), type_=sa.BIGINT())
    op.alter_column("user", "quota", existing_type=sa.INTEGER(), type_=sa.BIGINT())
    op.alter_column("user", "quota_count", existing_type=sa.INTEGER(), type_=sa.BIGINT())
    op.alter_column("sound", "file_size", existing_type=sa.INTEGER(), type_=sa.BIGINT())
    op.alter_column("sound", "transcode_file_size", existing_type=sa.INTEGER(), type_=sa.BIGINT())


def downgrade():
    op.alter_column("config", "user_quota", existing_type=sa.BIGINT(), type_=sa.INTEGER())
    op.alter_column("user", "quota", existing_type=sa.BIGINT(), type_=sa.INTEGER())
    op.alter_column("user", "quota_count", existing_type=sa.BIGINT(), type_=sa.INTEGER())
    op.alter_column("sound", "file_size", existing_type=sa.BIGINT(), type_=sa.INTEGER())
    op.alter_column("sound", "transcode_file_size", existing_type=sa.BIGINT(), type_=sa.INTEGER())
