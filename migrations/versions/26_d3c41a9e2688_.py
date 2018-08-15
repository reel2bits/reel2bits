"""Generate Actor for every User

Revision ID: d3c41a9e2688
Revises: 32f48de123f3
Create Date: 2018-08-05 10:47:58.540699

"""

# revision identifiers, used by Alembic.
revision = "d3c41a9e2688"
down_revision = "32f48de123f3"

from models import db, User, create_actor  # noqa: E402


def upgrade():
    for user in User.query.all():
        a = create_actor(user)
        a.user = user
        a.user_id = user.id
        db.session.add(a)
    db.session.commit()


def downgrade():
    pass
