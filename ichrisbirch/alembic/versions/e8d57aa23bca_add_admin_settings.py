"""Add admin settings, with signups seeded closed

`admin.settings` is the one row of settings an admin changes without a redeploy.
`POST /users/` reads `is_signup_open` on every request. The row starts closed,
so a database migrated here lets only an admin create an account until an admin
opens signups.

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
        'settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('is_signup_open', sa.Boolean(), nullable=False),
        sa.CheckConstraint('id = 1', name='single_row'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_settings')),
        schema='admin',
    )
    op.execute('INSERT INTO admin.settings (id, is_signup_open) VALUES (1, false)')


def downgrade() -> None:
    op.drop_table('settings', schema='admin')
