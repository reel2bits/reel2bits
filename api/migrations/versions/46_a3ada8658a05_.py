"""Set User.local == user.actor.local

Revision ID: a3ada8658a05
Revises: fc79fead3906
Create Date: 2019-09-06 13:18:57.269963

"""

# revision identifiers, used by Alembic.
revision = "a3ada8658a05"
down_revision = "fc79fead3906"

# from models import db, User  # noqa: E402


def upgrade():
    # for user in db.session.query(User).all():
    #     if len(user.actor) >= 1:
    #         if user.actor[0]:
    #             user.local = user.actor[0].is_local()
    # db.session.commit()
    pass


def downgrade():
    pass
