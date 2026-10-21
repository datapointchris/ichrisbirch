"""add autofix to issues and initiatives

Revision ID: 7a31418dc397
Revises: 7e7af73fb30a
Create Date: 2026-10-21 02:06:36.907676

The column defaults to true on the server, so an insert that never names it
succeeds.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '7a31418dc397'
down_revision: str | None = '7e7af73fb30a'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('initiatives', sa.Column('autofix', sa.Boolean(), nullable=False, server_default=sa.text('true')))
    op.add_column('issues', sa.Column('autofix', sa.Boolean(), nullable=False, server_default=sa.text('true')))


def downgrade() -> None:
    op.drop_column('issues', 'autofix')
    op.drop_column('initiatives', 'autofix')
