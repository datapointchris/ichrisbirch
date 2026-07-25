"""Add repo link to project_items

Links a project item to a repo in ~/dev/repos.json by registry name. Nullable
because most items are not repo work at all — home projects, things to sell,
errands — and those must stay first-class.

The link exists so completion can be cross-checked: repo items went stale
because nothing about doing the work brought you back to the item, while the
repo's own status.md stayed current. With the name recorded, tooling can flag
an open item whose repo already reports the work as done.

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-07-24

"""

import sqlalchemy as sa
from alembic import op

revision = 'e6f7a8b9c0d1'
down_revision = 'd5e6f7a8b9c0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('project_items', sa.Column('repo', sa.Text(), nullable=True))
    op.create_index('ix_project_items_repo', 'project_items', ['repo'])


def downgrade() -> None:
    op.drop_index('ix_project_items_repo', table_name='project_items')
    op.drop_column('project_items', 'repo')
