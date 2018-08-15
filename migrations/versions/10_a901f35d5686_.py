"""Add original filename for sounds

Revision ID: a901f35d5686
Revises: aeb6c1345690
Create Date: 2017-01-01 11:00:43.037746

"""

# revision identifiers, used by Alembic.
revision = "a901f35d5686"
down_revision = "aeb6c1345690"

import sqlalchemy as sa  # noqa: E402
from alembic import op  # noqa: E402


def upgrade():
    op.add_column(
        "sound", sa.Column("filename_orig", sa.String(length=255), nullable=True)
    )


def downgrade():
    op.drop_column("sound", "filename_orig")
