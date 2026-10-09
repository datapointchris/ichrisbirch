"""Add signup settings, seeded closed

`POST /users/` reads `admin.signup_settings.is_open` on every request, so an
admin opens or closes signups without a redeploy. The row starts closed, so a
database migrated here refuses signups until an admin opens them.

Revision ID: e8d57aa23bca
Revises: e0f1a2b3c4d5
Create Date: 2026-10-08 21:26:15.782882

"""

import sqlalchemy as sa
from alembic import op

revision = 'e8d57aa23bca'
down_revision = 'e0f1a2b3c4d5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'signup_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('is_open', sa.Boolean(), nullable=False),
        sa.CheckConstraint('id = 1', name='single_row'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_signup_settings')),
        schema='admin',
    )
    op.execute('INSERT INTO admin.signup_settings (id, is_open) VALUES (1, false)')


def downgrade() -> None:
    op.drop_table('signup_settings', schema='admin')
