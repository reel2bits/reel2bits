"""Set User.local == user.actor.local

Revision ID: a3ada8658a05
Revises: fc79fead3906
Create Date: 2019-09-06 13:18:57.269963

"""

# revision identifiers, used by Alembic.
revision = "a3ada8658a05"
down_revision = "fc79fead3906"


def upgrade():
    print("!!! Please run 'flask db-datas 002-set-local-users' for this data migration")


def downgrade():
    pass
