"""Drop personal_api_keys and jwt_refresh_tokens

Both tables hold credentials the API does not accept: personal API keys, and
the refresh tokens of JWTs it signed itself. Nothing reads or writes either.

The rows are not carried anywhere, so recovery is a database backup taken
before this ran. The downgrade rebuilds both tables empty, in the shape they
held before this ran.

This runs above the deploy's smoke gate, so a smoke failure leaves the previous
release serving with the tables gone. That release declares the two models and
queries neither.

Revision ID: 816ce25c08dc
Revises: 4ac06e1ade3e
Create Date: 2026-10-10

"""

import sqlalchemy as sa
from alembic import op

revision = '816ce25c08dc'
down_revision = '4ac06e1ade3e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table('personal_api_keys')
    op.drop_table('jwt_refresh_tokens')


def downgrade() -> None:
    op.create_table(
        'jwt_refresh_tokens',
        sa.Column('id', sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column('user_id', sa.Text(), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=False),
        sa.Column('date_stored', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_jwt_refresh_tokens')),
    )
    op.create_table(
        'personal_api_keys',
        sa.Column('id', sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('key_prefix', sa.Text(), nullable=False),
        sa.Column('hashed_key', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_personal_api_keys_user_id_users')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_personal_api_keys')),
        sa.UniqueConstraint('hashed_key', name=op.f('uq_personal_api_keys_hashed_key')),
    )
