"""Init default user quota

Revision ID: d37e30db3df1
Revises: 5bab69ccc222
Create Date: 2019-09-29 18:23:28.003355

"""

# revision identifiers, used by Alembic.
revision = "d37e30db3df1"
down_revision = "5bab69ccc222"

from models import db, User  # noqa: E402
from utils.defaults import Reel2bitsDefaults  # noqa: E402


def upgrade():
    for user in db.session.query(User).all():
        if not user.quota:
            user.quota = Reel2bitsDefaults.user_quotas_default
        if not user.quota_count:
            user.quota_count = 0
    db.session.commit()


def downgrade():
    pass
