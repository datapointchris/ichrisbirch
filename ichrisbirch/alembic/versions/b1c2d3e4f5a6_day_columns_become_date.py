"""Store a calendar day as a date

Six columns held a calendar day in a `timestamptz`. The value entered was a bare
`YYYY-MM-DD`, which Pydantic filled out to naive midnight and Postgres stored as
midnight UTC. Read back anywhere west of UTC that renders as the previous day, so
a book bought on the 20th displayed as the 19th. They become `date`, which is what
they always held.

The conversion pins UTC rather than relying on the session `TimeZone`, so it
recovers the day that was typed whatever the connection is set to. Every existing
value is exactly midnight UTC, so nothing is truncated.

Deployable alongside the previous release. A `Mapped[datetime]` model reading a
`date` column gets a `datetime.date`, which Pydantic promotes to midnight, and a
`datetime` written back is truncated to its day. The meaning of the column does
not change, which is what makes one deploy safe here — `events.date` changing from
an instant to a venue wall clock does change meaning, and ships separately.

Revision ID: b1c2d3e4f5a6
Revises: a2b3c4d5e6f7
Create Date: 2026-08-23

"""

import sqlalchemy as sa
from alembic import op

revision = 'b1c2d3e4f5a6'
down_revision = 'a2b3c4d5e6f7'
branch_labels = None
depends_on = None

# table, schema, columns
DAY_COLUMNS = [
    ('books', None, ['purchase_date', 'sell_date', 'read_start_date', 'read_finish_date']),
    ('coffee_shops', 'coffee', ['date_visited']),
    ('coffee_beans', 'coffee', ['purchase_date']),
]


def upgrade() -> None:
    for table, schema, columns in DAY_COLUMNS:
        for column in columns:
            op.alter_column(
                table,
                column,
                schema=schema,
                type_=sa.Date(),
                existing_type=sa.DateTime(timezone=True),
                existing_nullable=True,
                postgresql_using=f'({column} AT TIME ZONE \'UTC\')::date',
            )


def downgrade() -> None:
    # A day has no time of its own, so it goes back as midnight UTC — which is the
    # value that was there before, and the reason the columns were converted.
    for table, schema, columns in DAY_COLUMNS:
        for column in columns:
            op.alter_column(
                table,
                column,
                schema=schema,
                type_=sa.DateTime(timezone=True),
                existing_type=sa.Date(),
                existing_nullable=True,
                postgresql_using=f"{column}::timestamp AT TIME ZONE 'UTC'",
            )
