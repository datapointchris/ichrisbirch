"""Drop the issue tracker tables

The tracker's records live in slate, and no route, command or page here reads
these tables. Slate carries each record's number across and numbers new ones
from where `item_numbers` stood, so the sequence restarts above that range and a
new project item's number never names a slate record.

There is no way back in this chain. Recovery is the dump taken before this ran.

This is destructive and it runs above the deploy's verification gate, as
`d3e4f5a6b7c8_drop_the_chat_schema` explains. It is survivable because the
release before this one stopped reading the tables, so whichever color serves
reads none of them.

`icb_audit_trail` keeps the history of every dropped table. A drop fires no row
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
        '4aae4545efb4 drops the issue tracker tables and their rows. There is no downgrade — '
        'restore from the database dump taken before it ran.'
    )
