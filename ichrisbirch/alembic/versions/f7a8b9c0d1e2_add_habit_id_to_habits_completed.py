"""Link a habit completion to the habit it completed

`habits.completed` recorded only a name and category, never a reference to the
habit itself. Every consumer asking "is this habit done today" therefore had to
match on name + category, which breaks the moment a habit is renamed: the
completion no longer matches, and the habit reads as due again for the rest of
the day.

Nullable on purpose. A completion is a historical fact — it stays true after the
habit is deleted, which is why the name was denormalized in the first place. The
denormalized name and category stay exactly as they are; habit_id is added
alongside them so a live habit can be identified without string matching, and
history survives the habit going away.

The backfill matches existing rows on the same name + category pair the code
used, so completions of habits that still exist gain their link. Rows that match
nothing — habits since renamed or deleted — keep a null habit_id and go on being
read by name, which is what the fallback in consumers is for.

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-07-24

"""

import sqlalchemy as sa
from alembic import op

revision = 'f7a8b9c0d1e2'
down_revision = 'e6f7a8b9c0d1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('completed', sa.Column('habit_id', sa.Integer(), nullable=True), schema='habits')
    op.create_foreign_key(
        'fk_completed_habit_id',
        source_schema='habits',
        source_table='completed',
        referent_schema='habits',
        referent_table='habits',
        local_cols=['habit_id'],
        remote_cols=['id'],
        ondelete='SET NULL',
    )
    op.create_index('ix_habits_completed_habit_id', 'completed', ['habit_id'], schema='habits')

    # Only unambiguous pairs are linked: if two habits ever shared a name within
    # one category, matching by name cannot say which was completed, and a guess
    # is worse than the null the consumers already handle.
    op.execute(
        """
        UPDATE habits.completed AS c
        SET habit_id = h.id
        FROM habits.habits AS h
        WHERE h.name = c.name
          AND h.category_id = c.category_id
          AND (
            SELECT COUNT(*) FROM habits.habits AS dupe
            WHERE dupe.name = c.name AND dupe.category_id = c.category_id
          ) = 1
        """
    )


def downgrade() -> None:
    op.drop_index('ix_habits_completed_habit_id', 'completed', schema='habits')
    op.drop_constraint('fk_completed_habit_id', 'completed', schema='habits', type_='foreignkey')
    op.drop_column('completed', 'habit_id', schema='habits')
