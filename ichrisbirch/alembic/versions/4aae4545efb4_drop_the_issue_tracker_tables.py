"""Drop the issue tracker tables

The tracker's records live in slate, and no route, command or page here reads
these tables. Slate took over the records with their numbers, and its own
sequence continues from there. The restart puts project items above every number
slate held at the move. Slate's sequence has no ceiling, so the two ranges stay
apart only while slate is below the restart value.

There is no way back in this chain. Recovery needs a database dump taken before
this ran, and the deploy does not take one.
`docs/troubleshooting/deployment-issues.md` holds the restore under "Restore".

This is destructive and it runs above the deploy's verification gate, as
`d3e4f5a6b7c8_drop_the_chat_schema` explains. It is survivable because the
release before this one stopped reading the tables, so whichever color serves
reads none of them.

`icb_audit_trail` keeps the entries these tables wrote. A drop fires no row
trigger, and the triggers go with their tables.

Revision ID: 4aae4545efb4
Revises: 7a31418dc397
Create Date: 2026-11-03 03:40:00.000000+00:00

"""

from collections.abc import Sequence

from alembic import op

revision: str = '4aae4545efb4'
down_revision: str | None = '7a31418dc397'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Children before the tables their foreign keys name.
TRACKER_TABLES = (
    'issue_comments',
    'issue_label_assignments',
    'issue_labels',
    'issue_dependencies',
    'issues',
    'initiatives',
    'initiative_statuses',
    'issue_types',
    'issue_statuses',
)


def upgrade() -> None:
    for table in TRACKER_TABLES:
        op.drop_table(table)
    op.execute('ALTER SEQUENCE item_numbers RESTART WITH 100000')


def downgrade() -> None:
    raise NotImplementedError(
        '4aae4545efb4 drops the issue tracker tables and their rows. There is no downgrade. Restore a database '
        'dump taken before it ran, as docs/troubleshooting/deployment-issues.md says under "Restore".'
    )
