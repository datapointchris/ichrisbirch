"""Rename the project status 'done' to 'completed'

One word for one concept across the two resources. A project item stores
`completed`, and every reader that collapses an item's booleans into a status
prints that word; a project stored `done` for the same state, so the same idea
was spelled two ways on a resource and its own children.

`complete` is the verb on both — `icb projects complete` wrote a value called
`done`, which is the mismatch this removes.

The FK from projects.status makes this a two-step: insert the new lookup row,
repoint the projects that reference the old one, then drop it. Doing it in that
order means no row is ever left pointing at a name that is not there, so the
constraint holds throughout and the migration is safe to run against a live
table.

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
"""

from collections.abc import Sequence

from alembic import op

revision: str = 'd0e1f2a3b4c5'
down_revision: str | None = 'c9d0e1f2a3b4'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("INSERT INTO project_statuses (name) VALUES ('completed') ON CONFLICT DO NOTHING")
    op.execute("UPDATE projects SET status = 'completed' WHERE status = 'done'")
    op.execute("DELETE FROM project_statuses WHERE name = 'done'")


def downgrade() -> None:
    op.execute("INSERT INTO project_statuses (name) VALUES ('done') ON CONFLICT DO NOTHING")
    op.execute("UPDATE projects SET status = 'done' WHERE status = 'completed'")
    op.execute("DELETE FROM project_statuses WHERE name = 'completed'")
