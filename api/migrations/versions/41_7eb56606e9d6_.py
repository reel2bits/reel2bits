"""Generate flake ids for objects

Revision ID: 7eb56606e9d6
Revises: a8e2274a18d3
Create Date: 2019-07-06 07:55:00.474793

"""

# revision identifiers, used by Alembic.
revision = "7eb56606e9d6"
down_revision = "a8e2274a18d3"


def upgrade():
    print("!!! Please run 'flask db-datas 001-generate-tracks-uuids' for this data")


def downgrade():
    pass
