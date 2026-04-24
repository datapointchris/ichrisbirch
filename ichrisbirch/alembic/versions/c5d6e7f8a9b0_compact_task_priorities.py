"""Compact incomplete task priorities to dense rank 1..K.

Data-only migration. No DDL. Reinterprets the `priority` column from a
time-budget (days until overdue) to a positional rank (1 = top of list).
Existing negative and mixed-sign priorities are rewritten to a contiguous
1..K sequence ordered by `(priority ASC, add_date ASC)` across incomplete
tasks only. Completed tasks are left alone — their historical priority
values are preserved as-is.

Revision ID: c5d6e7f8a9b0
Revises: b4c5d6e7f8a9
Create Date: 2026-04-24
"""

from alembic import op

revision = 'c5d6e7f8a9b0'
down_revision = 'b4c5d6e7f8a9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        WITH ranked AS (
            SELECT id,
                   ROW_NUMBER() OVER (ORDER BY priority ASC, add_date ASC) AS new_priority
            FROM tasks
            WHERE complete_date IS NULL
        )
        UPDATE tasks
        SET priority = ranked.new_priority
        FROM ranked
        WHERE tasks.id = ranked.id;
        """
    )


def downgrade() -> None:
    # No-op: the pre-compaction mixed-sign priorities were artifacts of the
    # time-decay scheme and cannot be meaningfully restored from the
    # post-compaction ranks.
    pass
