"""Generate flake ids for objects

Revision ID: 7eb56606e9d6
Revises: a8e2274a18d3
Create Date: 2019-07-06 07:55:00.474793

"""

# revision identifiers, used by Alembic.
revision = "7eb56606e9d6"
down_revision = "a8e2274a18d3"

# from utils.flake_id import gen_flakeid  # noqa: E402
from sqlalchemy.dialects.postgresql import UUID  # noqa: E402
from sqlalchemy.sql import table, column  # noqa: E402

# from alembic import op  # noqa: E402


sound = table("sound", column("flake_id", UUID(as_uuid=True)))


def upgrade():
    # op.execute(
    #     sound.update().where(sound.flake_id.is_(None)).values({'flake_id': UUID(int=gen_flakeid())})
    # )
    pass


def downgrade():
    pass
