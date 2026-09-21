"""Store the day a habit was done as a date

`habits.completed.complete_date` held the moment a completion was clicked. The
fact it records is the day the habit was done, and every reader had to take a
zone to recover it: the day board windowed each day by the caller's zone, a
day filled in afterwards was stamped at local noon so it would land inside
that window, and the create validator allowed a day of slack for the noon
stamp. A `date` holds the day itself, so none of that is needed.

The conversion reads each moment in `COMPLETION_ZONE`, the zone the
completions were made in. Converting in UTC would move every completion made
in the evening west of UTC onto the next day.

Deployable alongside the previous release. A `Mapped[datetime]` model reading a
`date` column gets a `datetime.date`, which Pydantic promotes to midnight, and
a moment written back is cast to its day in the session `TimeZone`. The
previous release's day board compares the column against its own window, which
Postgres answers by promoting the day to midnight.

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-09-21

"""

import sqlalchemy as sa
from alembic import op

revision = 'f5a6b7c8d9e0'
down_revision = 'e4f5a6b7c8d9'
branch_labels = None
depends_on = None

COMPLETION_ZONE = 'America/New_York'


def upgrade() -> None:
    op.alter_column(
        'completed',
        'complete_date',
        schema='habits',
        type_=sa.Date(),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
        postgresql_using=f"(complete_date AT TIME ZONE '{COMPLETION_ZONE}')::date",
    )


def downgrade() -> None:
    # A day has no moment of its own, so it goes back as local noon in the same
    # zone, which is how the previous release stamped a day filled in afterwards.
    op.alter_column(
        'completed',
        'complete_date',
        schema='habits',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.Date(),
        existing_nullable=False,
        postgresql_using=f"(complete_date + time '12:00') AT TIME ZONE '{COMPLETION_ZONE}'",
    )
