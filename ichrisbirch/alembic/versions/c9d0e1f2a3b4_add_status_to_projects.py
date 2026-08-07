"""add status lookup table and terminal state to projects

Revision ID: c9d0e1f2a3b4
Revises: 87fb375b2531
Create Date: 2026-08-07

Every existing project backfills to `active`, which is what all of them were —
there was no way to say otherwise. Closing the finished ones is a data call made
through the API afterwards, not something a migration guesses at by name.

The global UNIQUE(name) is replaced by a unique index over active projects only.
Without that swap a completed `clisteno` keeps owning the name forever and
creating the next `clisteno` effort fails on the constraint before any
name-resolution rule is consulted.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'c9d0e1f2a3b4'
down_revision: str | None = '87fb375b2531'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'project_statuses',
        sa.Column('name', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('name', name=op.f('pk_project_statuses')),
    )
    op.execute("INSERT INTO project_statuses (name) VALUES ('active'), ('done'), ('dropped')")

    op.add_column('projects', sa.Column('status', sa.Text(), server_default='active', nullable=False))
    op.add_column('projects', sa.Column('status_reason', sa.Text(), nullable=True))
    op.add_column('projects', sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        op.f('fk_projects_status_project_statuses'), 'projects', 'project_statuses', ['status'], ['name']
    )
    op.create_check_constraint(
        'dropped_requires_reason',
        'projects',
        "status <> 'dropped' OR status_reason IS NOT NULL",
    )

    op.drop_constraint(op.f('uq_projects_name'), 'projects', type_='unique')
    op.create_index(
        'uq_projects_name_active',
        'projects',
        ['name'],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )


def downgrade() -> None:
    # Terminal projects may share a name with each other and with an active one,
    # which the global constraint cannot express. Suffix every terminal row with
    # its id so the constraint can be restored, rather than failing the
    # downgrade on data this schema has no way to hold.
    op.execute(
        """
        UPDATE projects
        SET name = name || ' (' || status || ' ' || left(id::text, 8) || ')'
        WHERE status <> 'active'
        """
    )
    op.drop_index('uq_projects_name_active', table_name='projects')
    op.create_unique_constraint(op.f('uq_projects_name'), 'projects', ['name'])

    op.drop_constraint('dropped_requires_reason', 'projects', type_='check')
    op.drop_constraint(op.f('fk_projects_status_project_statuses'), 'projects', type_='foreignkey')
    op.drop_column('projects', 'closed_at')
    op.drop_column('projects', 'status_reason')
    op.drop_column('projects', 'status')
    op.drop_table('project_statuses')
