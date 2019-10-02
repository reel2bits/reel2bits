"""Remove deprecated and unused ApiTokens

Revision ID: 6cd62c61bc1a
Revises: d37e30db3df1
Create Date: 2019-10-02 12:05:01.207728

"""

# revision identifiers, used by Alembic.
revision = "6cd62c61bc1a"
down_revision = "d37e30db3df1"

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade():
    op.drop_table("apitoken")


def downgrade():
    op.create_table(
        "apitoken",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("token", sa.VARCHAR(length=255), autoincrement=False, nullable=False),
        sa.Column("secret", sa.VARCHAR(length=255), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name="apitoken_user_id_fkey"),
        sa.PrimaryKeyConstraint("id", name="apitoken_pkey"),
        sa.UniqueConstraint("secret", name="apitoken_secret_key"),
        sa.UniqueConstraint("token", name="apitoken_token_key"),
    )
