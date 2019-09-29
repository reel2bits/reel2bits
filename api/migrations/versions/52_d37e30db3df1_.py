"""Init default user quota

Revision ID: d37e30db3df1
Revises: 5bab69ccc222
Create Date: 2019-09-29 18:23:28.003355

"""

# revision identifiers, used by Alembic.
revision = "d37e30db3df1"
down_revision = "5bab69ccc222"


def upgrade():
    print("!!! Please run 'flask db-datas 003-set-user-quota' for this data migration")


def downgrade():
    pass
