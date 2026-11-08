"""Drop the project tables

Projects and their items live in the projects app, which holds every row these
tables hold. No route, command or page here reads them. `item_numbers` goes with
them, because `project_items.number` was the last column drawing from it.

There is no way back in this chain. Recovery needs a database dump taken before
this ran, and the deploy does not take one.
`docs/troubleshooting/deployment-issues.md` holds the restore under "Restore".

This is destructive and it runs above the deploy's verification gate, as
`d3e4f5a6b7c8_drop_the_chat_schema` explains. It is survivable because the
release before this one stopped reading the tables, so whichever color serves
reads none of them.

`icb_audit_trail` keeps the entries these tables wrote. A drop fires no row
trigger, and the triggers go with their tables.

Revision ID: c6092e8133ed
Revises: 4aae4545efb4
Create Date: 2026-11-08 15:52:01.958228+00:00

"""

from collections.abc import Sequence

from alembic import op

revision: str = 'c6092e8133ed'
down_revision: str | None = '4aae4545efb4'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Children before the tables their foreign keys name.
PROJECT_TABLES = (
    'project_item_tasks',
    'project_item_dependencies',
    'project_item_memberships',
    'project_items',
    'projects',
    'project_statuses',
    'project_kinds',
)


def upgrade() -> None:
    for table in PROJECT_TABLES:
        op.drop_table(table)
    op.execute('DROP SEQUENCE item_numbers')


def downgrade() -> None:
    raise NotImplementedError(
        'c6092e8133ed drops the project tables and their rows. There is no downgrade. Restore a database '
        'dump taken before it ran, as docs/troubleshooting/deployment-issues.md says under "Restore".'
    )
