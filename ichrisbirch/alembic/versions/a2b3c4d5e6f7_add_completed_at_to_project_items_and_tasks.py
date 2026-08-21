"""Add completed_at to project_items and project_item_tasks

Completion was a bare boolean, so the only timestamp near it was `updated_at` —
which complete, edit, reopen, archive and unarchive all bump. "What did I finish
this week" could therefore only be approximated, and the approximation counted
every edit to a finished item as a fresh completion.

Nullable, and left null for every row that already exists. A completion date
inferred from `updated_at` would be a fabricated fact rather than a missing one,
and a reader that has to handle null anyway gains nothing from the guess.

Additive and backward-compatible, which blue/green requires: the colour still
serving never selects the column, and the column has no default to conflict with.

Revision ID: a2b3c4d5e6f7
Revises: d0e1f2a3b4c5
Create Date: 2026-08-20

"""

import sqlalchemy as sa
from alembic import op

revision = 'a2b3c4d5e6f7'
down_revision = 'd0e1f2a3b4c5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('project_items', sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('project_item_tasks', sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('project_item_tasks', 'completed_at')
    op.drop_column('project_items', 'completed_at')
