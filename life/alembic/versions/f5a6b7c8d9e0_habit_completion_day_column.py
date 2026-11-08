"""Add the day a habit was done as its own date column

`habits.completed.complete_date` holds the moment a completion was clicked. The
fact it records is the day the habit was done, so `completion_date` holds that
day as a `date`. It is filled from each moment read in `COMPLETION_ZONE`, the
zone the completions were made in. Reading them in UTC would move every
completion made in the evening west of UTC onto the next day.

The type is not changed in place. The previous release keeps serving while this
runs, and after it when the smoke gate fails. That release compares
`complete_date` against a window of instants and writes a moment into it. A
`date` column would take both through a cast in the session `TimeZone`, so every
New York completion would read as not done, and an evening click would be
stored as the next day.

A trigger keeps the two columns in step, whichever release writes. A row given
only `complete_date`, as the previous release writes it, gets that moment's day
in `COMPLETION_ZONE`. A row given only `completion_date` gets noon of that day
there. The previous release stamps a day filled in afterwards the same way, and
reads the row on the right day. The trigger and `complete_date` last only while
a release that reads `complete_date` can still serve.

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

KEEP_IN_STEP = f"""
CREATE FUNCTION habits.keep_completion_columns_in_step() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        IF NEW.completion_date IS DISTINCT FROM OLD.completion_date
           AND NEW.complete_date IS NOT DISTINCT FROM OLD.complete_date THEN
            NEW.complete_date := NULL;
        ELSIF NEW.complete_date IS DISTINCT FROM OLD.complete_date
           AND NEW.completion_date IS NOT DISTINCT FROM OLD.completion_date THEN
            NEW.completion_date := NULL;
        END IF;
    END IF;
    IF NEW.completion_date IS NULL THEN
        NEW.completion_date := (NEW.complete_date AT TIME ZONE '{COMPLETION_ZONE}')::date;
    END IF;
    IF NEW.complete_date IS NULL THEN
        NEW.complete_date := (NEW.completion_date + time '12:00') AT TIME ZONE '{COMPLETION_ZONE}';
    END IF;
    RETURN NEW;
END
$$
"""


def upgrade() -> None:
    op.add_column('completed', sa.Column('completion_date', sa.Date(), nullable=True), schema='habits')
    op.execute(f"UPDATE habits.completed SET completion_date = (complete_date AT TIME ZONE '{COMPLETION_ZONE}')::date")
    op.execute(KEEP_IN_STEP)
    op.execute(
        'CREATE TRIGGER keep_completion_columns_in_step BEFORE INSERT OR UPDATE ON habits.completed '
        'FOR EACH ROW EXECUTE FUNCTION habits.keep_completion_columns_in_step()'
    )
    # Safe for the previous release too: the trigger fills the day on every row it writes.
    op.alter_column('completed', 'completion_date', nullable=False, schema='habits')


def downgrade() -> None:
    op.execute('DROP TRIGGER keep_completion_columns_in_step ON habits.completed')
    op.execute('DROP FUNCTION habits.keep_completion_columns_in_step()')
    op.drop_column('completed', 'completion_date', schema='habits')
