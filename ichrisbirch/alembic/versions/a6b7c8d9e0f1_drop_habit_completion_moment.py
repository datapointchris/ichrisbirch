"""Drop the moment column beside a habit completion's day

`habits.completed.completion_date` holds the day a habit was done. The release
serving while this runs maps `HabitCompleted.complete_date` onto it and never
reads the `complete_date` column. That column held the moment for the release
before, and `keep_completion_columns_in_step` filled it. The trigger's function
names the column, so the two go first. Left behind, it fails every write.

This must run in a deploy after `f5a6b7c8d9e0`'s. Run in the same upgrade, it
drops the column the release still serving reads. It runs above the smoke gate.
A failed gate leaves `f5a6b7c8d9e0`'s release serving, which never reads it.

The stored moments do not come back. The downgrade rebuilds the column, the
function and the trigger as `f5a6b7c8d9e0` left them, and gives each row noon of
its day in `COMPLETION_ZONE`. That is what the trigger gave a row written with
only a day. The original moments are only in a database backup taken before
this ran.

Revision ID: a6b7c8d9e0f1
Revises: f5a6b7c8d9e0
Create Date: 2026-09-21

"""

import sqlalchemy as sa
from alembic import op

revision = 'a6b7c8d9e0f1'
down_revision = 'f5a6b7c8d9e0'
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
    op.execute('DROP TRIGGER keep_completion_columns_in_step ON habits.completed')
    op.execute('DROP FUNCTION habits.keep_completion_columns_in_step()')
    op.drop_column('completed', 'complete_date', schema='habits')


def downgrade() -> None:
    op.add_column('completed', sa.Column('complete_date', sa.DateTime(timezone=True), nullable=True), schema='habits')
    op.execute(f"UPDATE habits.completed SET complete_date = (completion_date + time '12:00') AT TIME ZONE '{COMPLETION_ZONE}'")
    op.alter_column('completed', 'complete_date', nullable=False, schema='habits')
    op.execute(KEEP_IN_STEP)
    op.execute(
        'CREATE TRIGGER keep_completion_columns_in_step BEFORE INSERT OR UPDATE ON habits.completed '
        'FOR EACH ROW EXECUTE FUNCTION habits.keep_completion_columns_in_step()'
    )
