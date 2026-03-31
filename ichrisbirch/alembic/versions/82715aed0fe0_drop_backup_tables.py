"""Drop backup_history and backup_restores tables

Revision ID: 82715aed0fe0
Revises: b2c3d4e5f6a7
Create Date: 2026-03-31
"""

from alembic import op

revision = '82715aed0fe0'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table('backup_restores', schema='admin')
    op.drop_table('backup_history', schema='admin')


def downgrade() -> None:
    pass
