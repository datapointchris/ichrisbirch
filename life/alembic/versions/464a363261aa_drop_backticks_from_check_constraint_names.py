"""Drop the backticks from every check constraint's name

The `ck` naming convention wrapped each constraint's own name in backticks,
and Postgres kept them as part of the name: ck_tasks_`window_days_positive`.
`database/base.py` spells it ck_tasks_window_days_positive, and this renames
every backticked check constraint to that spelling.

The upgrade finds its targets in `pg_constraint`. Production's set has never
been read, and a list naming a constraint it lacks would fail the deploy. Each
rename is logged, so the deploy log records production's set.

The migrations that create these constraints pin the backticked names with
`op.f()`. A replay would otherwise build them under the current convention,
and this upgrade would rename nothing in any test.

The downgrade puts the backticks back on `BACKTICKED_IN_A_REPLAY`, the set a
replay to `e8d57aa23bca` builds. The older migrations drop their constraints
by those names.

No code names a check constraint, so the release serving while this runs is
unaffected.

Revision ID: 464a363261aa
Revises: e8d57aa23bca
Create Date: 2026-10-08 23:03:08.388264

"""

import logging

import sqlalchemy as sa
from alembic import op

revision = '464a363261aa'
down_revision = 'e8d57aa23bca'
branch_labels = None
depends_on = None

logger = logging.getLogger('alembic.runtime.migration')

BACKTICKED_CHECK_CONSTRAINTS = sa.text(
    """
    SELECT n.nspname, t.relname, c.conname
    FROM pg_constraint c
    JOIN pg_class t ON t.oid = c.conrelid
    JOIN pg_namespace n ON n.oid = t.relnamespace
    WHERE c.contype = 'c' AND strpos(c.conname, '`') > 0
    ORDER BY n.nspname, t.relname, c.conname
    """
)

BACKTICKED_IN_A_REPLAY = (
    ('admin', 'settings', 'single_row'),
    ('public', 'autotasks', 'window_days_positive'),
    ('public', 'initiatives', 'initiative_dropped_requires_reason'),
    ('public', 'initiatives', 'initiative_priority_range'),
    ('public', 'issue_dependencies', 'issue_no_self_dependency'),
    ('public', 'issue_labels', 'issue_label_group_slug_shape'),
    ('public', 'issue_labels', 'issue_label_slug_shape'),
    ('public', 'issues', 'issue_canceled_requires_reason'),
    ('public', 'issues', 'issue_claim_is_whole'),
    ('public', 'issues', 'issue_claim_only_in_progress'),
    ('public', 'issues', 'issue_closed_ts_only_when_closed'),
    ('public', 'issues', 'issue_duplicate_only_when_canceled'),
    ('public', 'issues', 'issue_not_discovered_from_itself'),
    ('public', 'issues', 'issue_not_duplicate_of_itself'),
    ('public', 'issues', 'issue_not_own_parent'),
    ('public', 'issues', 'issue_priority_range'),
    ('public', 'issues', 'issue_reason_only_when_canceled'),
    ('public', 'project_item_dependencies', 'no_self_dependency'),
    ('public', 'projects', 'dropped_requires_reason'),
    ('public', 'strains', 'rating_range'),
    ('public', 'task_categories', 'window_days_positive'),
    ('public', 'tasks', 'drop_reason_needs_drop_date'),
    ('public', 'tasks', 'one_closed_state'),
    ('public', 'tasks', 'pinned_only_open'),
    ('public', 'tasks', 'window_days_positive'),
)


def rename_constraint(schema: str, table: str, old: str, new: str) -> None:
    quote = op.get_bind().dialect.identifier_preparer.quote_identifier
    op.execute(f'ALTER TABLE {quote(schema)}.{quote(table)} RENAME CONSTRAINT {quote(old)} TO {quote(new)}')


def upgrade() -> None:
    for schema, table, name in op.get_bind().execute(BACKTICKED_CHECK_CONSTRAINTS).all():
        clean = name.replace('`', '')
        rename_constraint(schema, table, name, clean)
        logger.info('Renamed check constraint %s on %s.%s to %s', name, schema, table, clean)


def downgrade() -> None:
    for schema, table, name in BACKTICKED_IN_A_REPLAY:
        rename_constraint(schema, table, f'ck_{table}_{name}', f'ck_{table}_`{name}`')
