"""Each table of the projects database the copy writes, and the projection of icb's dumped rows it must equal.

`source` is a SELECT over the `dumped_` tables yielding `columns`. The copy inserts it, and the proof
compares it with `target`, the same columns read back from the table. `carries` counts the dumped rows
the source must carry one for one, so a filter cannot drop a row unnoticed.

That proof shares `source` with the insert, so it cannot see a column the source puts in the wrong
place. A second proof reads each column the table keeps from its `counterpart` straight from both
tables, matched by name, and leaves only the `reshaped` columns to the first.

`columns` lists every column of the table, and the copy refuses a database whose catalog says
otherwise. Tables are listed in the order their foreign keys need.
"""

from __future__ import annotations

import dataclasses as dc
from collections.abc import Iterable

from ichrisbirch.copy_projects_to_new_database.dumped_icb_tables import PROJECT_TABLES


def quoted(names: Iterable[str]) -> str:
    return ', '.join(f'"{name}"' for name in names)


@dc.dataclass(frozen=True)
class TargetTable:
    name: str
    columns: tuple[str, ...]
    source: str
    carries: str
    # Narrows the target read to the copied rows, where the table may already hold the database's own.
    target_filter: str = ''
    # The dumped icb table whose columns this table keeps by name.
    counterpart: str | None = None
    # Columns the source computes rather than keeps, which only the source proof can read.
    reshaped: frozenset[str] = frozenset()
    # What an insert does with a row the database already holds.
    on_conflict: str = ''

    def kept_by_name(self, counterpart_columns: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(column for column in self.columns if column not in self.reshaped and column in counterpart_columns)

    @property
    def column_list(self) -> str:
        return quoted(self.columns)

    @property
    def projection(self) -> str:
        """The source as a FROM item whose columns carry the target's names."""
        return f'({self.source}) AS projected ({self.column_list})'

    @property
    def insert(self) -> str:
        # OVERRIDING SYSTEM VALUE writes an id an identity column declared ALWAYS would refuse.
        return f'INSERT INTO {self.name} ({self.column_list}) OVERRIDING SYSTEM VALUE {self.source} {self.on_conflict}'

    @property
    def target(self) -> str:
        return f'SELECT {self.column_list} FROM {self.name} {self.target_filter}'


def copied_as_dumped(name: str, columns: tuple[str, ...]) -> TargetTable:
    return TargetTable(
        name,
        columns,
        source=f'SELECT {quoted(columns)} FROM dumped_{name}',
        carries=f'SELECT count(*) FROM dumped_{name}',
        counterpart=name,
    )


# `projects-api migrate` seeds each kind and status its model knows, so a copied row may meet one already held.
def lookup(name: str) -> TargetTable:
    return dc.replace(
        copied_as_dumped(name, ('name',)),
        target_filter=f'WHERE name IN (SELECT name FROM dumped_{name})',
        on_conflict='ON CONFLICT (name) DO NOTHING',
    )


PROJECT_KINDS = lookup('project_kinds')
PROJECT_STATUSES = lookup('project_statuses')
PROJECTS = copied_as_dumped(
    'projects', ('id', 'name', 'description', 'kind', 'status', 'status_reason', 'closed_at', 'position', 'created_at')
)
PROJECT_ITEMS = copied_as_dumped(
    'project_items', ('id', 'number', 'title', 'notes', 'repo', 'completed', 'completed_at', 'archived', 'created_at', 'updated_at')
)
PROJECT_ITEM_MEMBERSHIPS = copied_as_dumped('project_item_memberships', ('item_id', 'project_id', 'position'))
PROJECT_ITEM_DEPENDENCIES = copied_as_dumped('project_item_dependencies', ('item_id', 'depends_on_id'))
PROJECT_ITEM_TASKS = copied_as_dumped(
    'project_item_tasks', ('id', 'item_id', 'title', 'completed', 'completed_at', 'position', 'created_at')
)

# Every row keeps icb's table name, record id, actor and changes as written, in icb's order, under ids
# that follow the rows the database's own history already holds. icb recorded no trace, so each row's is null.
AUDIT_TRAIL = TargetTable(
    'audit_trail',
    (
        'id',
        'changed_at',
        'table_name',
        'record_id',
        'operation',
        'changes',
        'actor',
        'request_id',
        'job_run_id',
        'traceparent',
        'baggage',
    ),
    source="""
        SELECT %(audit_baseline)s::bigint + row_number() OVER (ORDER BY changed_at, id), changed_at, table_name, record_id,
            operation, changes, actor, request_id, job_run_id, NULL::text, NULL::text
        FROM dumped_icb_audit_trail
    """,
    carries='SELECT count(*) FROM dumped_icb_audit_trail',
    target_filter='WHERE id > %(audit_baseline)s::bigint',
    counterpart='icb_audit_trail',
    reshaped=frozenset({'id'}),
)

# Ordered by PROJECT_TABLES, the list whose history the copy keeps, so the two cannot name different tables.
COPIED_TABLES = tuple(
    {
        table.name: table
        for table in (
            PROJECT_KINDS,
            PROJECT_STATUSES,
            PROJECTS,
            PROJECT_ITEMS,
            PROJECT_ITEM_MEMBERSHIPS,
            PROJECT_ITEM_DEPENDENCIES,
            PROJECT_ITEM_TASKS,
        )
    }[name]
    for name in PROJECT_TABLES
)
TARGET_TABLES = (*COPIED_TABLES, AUDIT_TRAIL)

# The tables that must be empty before the copy. The lookups and the audit trail may hold the database's own rows.
HOLDING_PROJECT_ROWS = tuple(table for table in COPIED_TABLES if table.on_conflict == '')
