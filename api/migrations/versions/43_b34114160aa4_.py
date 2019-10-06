"""Generate flake ids for albums

Revision ID: b34114160aa4
Revises: 8b4238e4e1a3
Create Date: 2019-07-12 18:12:16.228463

"""

# revision identifiers, used by Alembic.
revision = "b34114160aa4"
down_revision = "8b4238e4e1a3"


def upgrade():
    print("!!! Please run 'flask db-datas 006-generate-albums-uuids' for this data migration")


def downgrade():
    pass
