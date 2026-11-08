"""Store an event as a wall clock at its venue, with the zone that resolves it

`events.date` held an instant. An event is not one: doors at 19:00 are 19:00 for
every reader, and stay 19:00 if a government moves the offset before the date
arrives. Storing the instant means the reading depends on who is looking.

The form is a `datetime-local` input, so it sent 19:00 with no offset, and the
old validator handed that to a parser that assumed UTC. Entering 7pm stored
19:00Z and displayed 3pm anywhere four hours west.

The column becomes naive and `timezone` holds the IANA name that resolves it. An
IANA name rather than an offset, because an offset cannot say what the local time
will be on a date that has not happened yet.

Existing rows keep the reading that was entered: the old validator forced the
naive form value to UTC, so `AT TIME ZONE 'UTC'` returns what the user typed.
Their `timezone` becomes 'UTC' because nothing recorded which zone was meant —
the time shown is right and the label may not be, which is correctable per row
and was not correctable at all before.

Not deployable alongside the previous release, and that is why it ships on its
own. The column's meaning changes, so the old code reads a wall clock as an
instant. `prod-rollback` has no downgrade verb, so a rollback needs this
migration reversed by hand.

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-08-24

"""

import sqlalchemy as sa
from alembic import op

revision = 'c2d3e4f5a6b7'
down_revision = 'b1c2d3e4f5a6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('events', sa.Column('timezone', sa.Text(), nullable=False, server_default='UTC'))
    op.alter_column(
        'events',
        'date',
        type_=sa.DateTime(timezone=False),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
        postgresql_using="date AT TIME ZONE 'UTC'",
    )


def downgrade() -> None:
    # The wall clock goes back as a UTC instant, which is what the column held
    # before — right for a row that really was UTC, and wrong by the offset for
    # one that was not. The zone that would have made it right is dropped with
    # the column, so this is lossy in the same way the original storage was.
    op.alter_column(
        'events',
        'date',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(timezone=False),
        existing_nullable=False,
        postgresql_using="date AT TIME ZONE 'UTC'",
    )
    op.drop_column('events', 'timezone')
