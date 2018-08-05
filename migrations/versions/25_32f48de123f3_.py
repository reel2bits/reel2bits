"""Add actor federation

Revision ID: 32f48de123f3
Revises: be5369fae219
Create Date: 2018-08-05 10:42:47.048304

"""

# revision identifiers, used by Alembic.
revision = '32f48de123f3'
down_revision = 'be5369fae219'

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402
import sqlalchemy_utils  # noqa: E402
from models import ACTOR_TYPE_CHOICES  # noqa: E402


def upgrade():
    op.create_table('actor',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('url', sqlalchemy_utils.types.url.URLType(),
                              nullable=True),
                    sa.Column('outbox_url',
                              sqlalchemy_utils.types.url.URLType(),
                              nullable=True),
                    sa.Column('inbox_url',
                              sqlalchemy_utils.types.url.URLType(),
                              nullable=True),
                    sa.Column('following_url',
                              sqlalchemy_utils.types.url.URLType(),
                              nullable=True),
                    sa.Column('followers_url',
                              sqlalchemy_utils.types.url.URLType(),
                              nullable=True),
                    sa.Column('shared_inbox_url',
                              sqlalchemy_utils.types.url.URLType(),
                              nullable=True),
                    sa.Column('type', sqlalchemy_utils.types.choice.ChoiceType(
                        choices=ACTOR_TYPE_CHOICES),
                              server_default='Person', nullable=True),
                    sa.Column('name', sa.String(length=200), nullable=True),
                    sa.Column('domain', sa.String(length=1000),
                              nullable=False),
                    sa.Column('summary', sa.String(length=500), nullable=True),
                    sa.Column('preferred_username', sa.String(length=200),
                              nullable=True),
                    sa.Column('public_key', sa.String(length=5000),
                              nullable=True),
                    sa.Column('private_key', sa.String(length=5000),
                              nullable=True),
                    sa.Column('creation_date', sa.DateTime(), nullable=True),
                    sa.Column('last_fetch_date', sa.DateTime(), nullable=True),
                    sa.Column('manually_approves_followers', sa.Boolean(),
                              nullable=True),
                    sa.Column('user_id', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('domain', 'preferred_username',
                                        name='_domain_pref_username_uc')
                    )
    op.create_index(op.f('ix_actor_url'), 'actor', ['url'], unique=True)


def downgrade():
    op.drop_index(op.f('ix_actor_url'), table_name='actor')
    op.drop_table('actor')
