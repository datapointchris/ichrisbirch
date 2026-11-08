"""add kind lookup table and projects.kind

Revision ID: a7b8c9d0e1f2
Revises: f7a8b9c0d1e2
Create Date: 2026-08-05

Backfills every existing project to `build`, which is what nearly all of them
are. The two that are not get corrected through the API afterwards — a data
call the migration has no business guessing at by name matching.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'a7b8c9d0e1f2'
down_revision: str | None = 'f7a8b9c0d1e2'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'project_kinds',
        sa.Column('name', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('name', name=op.f('pk_project_kinds')),
    )
    op.execute("INSERT INTO project_kinds (name) VALUES ('build'), ('chore'), ('life')")
    op.add_column('projects', sa.Column('kind', sa.Text(), server_default='build', nullable=False))
    op.create_foreign_key(op.f('fk_projects_kind_project_kinds'), 'projects', 'project_kinds', ['kind'], ['name'])


def downgrade() -> None:
    op.drop_constraint(op.f('fk_projects_kind_project_kinds'), 'projects', type_='foreignkey')
    op.drop_column('projects', 'kind')
    op.drop_table('project_kinds')
