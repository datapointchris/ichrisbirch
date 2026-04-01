"""Convert serial columns to identity columns

All integer primary key columns are converted from SERIAL (implicit sequence +
DEFAULT nextval()) to GENERATED ALWAYS AS IDENTITY. This makes the sequence
intrinsic to the column, simplifies permission management, and prevents
accidental manual ID inserts that could desync the sequence.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-01
"""

from alembic import op

revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None

# (schema, table, column, sequence_name)
SERIAL_COLUMNS = [
    (None, 'articles', 'id', 'articles_id_seq'),
    (None, 'article_failed_imports', 'id', 'article_failed_imports_id_seq'),
    (None, 'autotasks', 'id', 'autotasks_id_seq'),
    (None, 'books', 'id', 'books_id_seq'),
    (None, 'countdowns', 'id', 'countdowns_id_seq'),
    (None, 'durations', 'id', 'durations_id_seq'),
    (None, 'duration_notes', 'id', 'duration_notes_id_seq'),
    (None, 'events', 'id', 'events_id_seq'),
    (None, 'jwt_refresh_tokens', 'id', 'jwt_refresh_tokens_id_seq'),
    (None, 'money_wasted', 'id', 'money_wasted_id_seq'),
    (None, 'personal_api_keys', 'id', 'personal_api_keys_id_seq'),
    (None, 'tasks', 'id', 'tasks_id_seq'),
    (None, 'users', 'id', 'users_id_seq'),
    ('admin', 'scheduler_job_runs', 'id', 'admin.scheduler_job_runs_id_seq'),
    ('box_packing', 'boxes', 'id', 'box_packing.boxes_id_seq'),
    ('box_packing', 'items', 'id', 'box_packing.items_id_seq'),
    ('chat', 'chats', 'id', 'chat.chats_id_seq'),
    ('chat', 'messages', 'id', 'chat.messages_id_seq'),
    ('habits', 'categories', 'id', 'habits.categories_id_seq'),
    ('habits', 'completed', 'id', 'habits.completed_id_seq'),
    ('habits', 'habits', 'id', 'habits.habits_id_seq'),
]


def _qualified(schema, table):
    """Return schema-qualified table name."""
    return f'{schema}.{table}' if schema else table


def upgrade() -> None:
    for schema, table, column, seq_name in SERIAL_COLUMNS:
        qualified = _qualified(schema, table)
        # 1. Get current sequence value so identity restarts correctly
        # 2. Drop the DEFAULT (removes nextval() binding)
        # 3. Drop the old sequence
        # 4. Add identity column with correct restart value
        op.execute(f"""
            DO $$
            DECLARE
                next_val bigint;
            BEGIN
                SELECT COALESCE(MAX({column}), 0) + 1 INTO next_val FROM {qualified};
                EXECUTE format('ALTER TABLE {qualified} ALTER COLUMN {column} DROP DEFAULT');
                EXECUTE format('DROP SEQUENCE IF EXISTS {seq_name}');
                EXECUTE format(
                    'ALTER TABLE {qualified} ALTER COLUMN {column} ADD GENERATED ALWAYS AS IDENTITY (RESTART %s)',
                    next_val
                );
            END $$;
        """)  # nosec B608 - values are hardcoded constants, not user input


def downgrade() -> None:
    for schema, table, column, seq_name in SERIAL_COLUMNS:
        qualified = _qualified(schema, table)
        # Revert: drop identity, recreate sequence, set default
        op.execute(f"""
            DO $$
            DECLARE
                next_val bigint;
            BEGIN
                SELECT COALESCE(MAX({column}), 0) + 1 INTO next_val FROM {qualified};
                EXECUTE format('ALTER TABLE {qualified} ALTER COLUMN {column} DROP IDENTITY IF EXISTS');
                EXECUTE format('CREATE SEQUENCE {seq_name} START %s', next_val);
                EXECUTE format('ALTER TABLE {qualified} ALTER COLUMN {column} SET DEFAULT nextval(''{seq_name}'')');
                EXECUTE format('ALTER SEQUENCE {seq_name} OWNED BY {qualified}.{column}');
            END $$;
        """)  # nosec B608 - values are hardcoded constants, not user input
