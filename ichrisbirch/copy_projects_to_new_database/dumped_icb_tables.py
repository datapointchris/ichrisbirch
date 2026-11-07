"""icb's project rows as a dump holds them, loaded into tables that live only for the copy's transaction.

Each table names every column this copy was written for. A dump whose COPY header lists any other set
is refused, so a column added to icb after this copy was written cannot be dropped without notice.
The column types come from icb's own models.
"""

from __future__ import annotations

import dataclasses as dc
from collections.abc import Callable

import psycopg
from psycopg import sql
from sqlalchemy.dialects import postgresql

from ichrisbirch.copy_projects_to_new_database.copy_refused import CopyRefused
from ichrisbirch.copy_projects_to_new_database.plain_pg_dump import PlainDump
from ichrisbirch.database.base import Base
from ichrisbirch.models.project import Project
from ichrisbirch.models.project import ProjectItem
from ichrisbirch.models.project import ProjectItemDependency
from ichrisbirch.models.project import ProjectItemMembership
from ichrisbirch.models.project import ProjectItemTask
from ichrisbirch.models.project import ProjectKind
from ichrisbirch.models.project import ProjectStatus
from ichrisbirch.models.record_change import RecordChange

# Every table the copy moves, lookups included, in the order their foreign keys need.
# Their rows in icb's audit trail are the history the copy carries.
PROJECT_TABLES = (
    'project_kinds',
    'project_statuses',
    'projects',
    'project_items',
    'project_item_memberships',
    'project_item_dependencies',
    'project_item_tasks',
)


@dc.dataclass(frozen=True)
class DumpedTable:
    name: str
    model: type[Base]
    columns: tuple[str, ...]

    @property
    def loaded_as(self) -> str:
        return f'dumped_{self.name}'

    def create_statement(self) -> sql.Composed:
        table = self.model.__table__
        dialect = postgresql.dialect()
        columns = sql.SQL(', ').join(
            sql.SQL('{} {}').format(sql.Identifier(name), sql.SQL(str(table.c[name].type.compile(dialect=dialect))))
            for name in self.columns
        )
        return sql.SQL('CREATE TEMPORARY TABLE {} ({}) ON COMMIT DROP').format(sql.Identifier(self.loaded_as), columns)

    def copy_statement(self, columns: tuple[str, ...]) -> sql.Composed:
        return sql.SQL('COPY {} ({}) FROM STDIN').format(sql.Identifier(self.loaded_as), sql.SQL(', ').join(map(sql.Identifier, columns)))

    def refuse_other_columns(self, dumped: tuple[str, ...]) -> None:
        unmapped = sorted(set(dumped) - set(self.columns))
        missing = sorted(set(self.columns) - set(dumped))
        if unmapped or missing:
            raise CopyRefused(
                f'the dump holds icb {self.name} in another shape than this copy was written for: '
                f'columns it maps nothing to {unmapped}, columns it expects and the dump lacks {missing}'
            )


DUMPED_TABLES = (
    DumpedTable('project_kinds', ProjectKind, ('name',)),
    DumpedTable('project_statuses', ProjectStatus, ('name',)),
    DumpedTable(
        'projects',
        Project,
        ('id', 'name', 'description', 'kind', 'status', 'status_reason', 'closed_at', 'position', 'created_at'),
    ),
    DumpedTable(
        'project_items',
        ProjectItem,
        ('id', 'number', 'title', 'notes', 'repo', 'completed', 'completed_at', 'archived', 'created_at', 'updated_at'),
    ),
    DumpedTable('project_item_memberships', ProjectItemMembership, ('item_id', 'project_id', 'position')),
    DumpedTable('project_item_dependencies', ProjectItemDependency, ('item_id', 'depends_on_id')),
    DumpedTable(
        'project_item_tasks',
        ProjectItemTask,
        ('id', 'item_id', 'title', 'completed', 'completed_at', 'position', 'created_at'),
    ),
    # Every app's history shares this table, so only the project tables' rows are kept.
    DumpedTable(
        'icb_audit_trail',
        RecordChange,
        ('id', 'changed_at', 'table_name', 'record_id', 'operation', 'changes', 'actor', 'request_id', 'job_run_id'),
    ),
)
DUMPED_BY_NAME = {table.name: table for table in DUMPED_TABLES}


@dc.dataclass(frozen=True)
class LoadedRows:
    table: str
    rows_read: int
    rows_kept: int


def load_dumped_projects(cursor: psycopg.Cursor, dump: PlainDump) -> dict[str, LoadedRows]:
    """Load every project row the dump holds, and read past every other table's rows without sending them anywhere."""
    for table in DUMPED_TABLES:
        cursor.execute(table.create_statement())
    loaded: dict[str, LoadedRows] = {}
    for block in dump.copy_blocks():
        dumped = DUMPED_BY_NAME.get(block.table)
        if dumped is None:
            continue
        dumped.refuse_other_columns(block.columns)
        keeps_row = project_history_filter(block.columns) if dumped.name == 'icb_audit_trail' else None
        kept = 0
        with cursor.copy(dumped.copy_statement(block.columns)) as copy:
            for row in block.rows():
                if keeps_row is None or keeps_row(row):
                    copy.write(row)
                    kept += 1
        loaded[dumped.name] = LoadedRows(dumped.name, block.rows_read, kept)
    if not dump.complete:
        raise CopyRefused("the dump ends before pg_dump's closing line, so it was cut short, perhaps while still being written")
    missing = [table.name for table in DUMPED_TABLES if table.name not in loaded]
    if missing:
        raise CopyRefused(f'the dump holds no COPY block for icb {", ".join(missing)}')
    return loaded


def project_history_filter(columns: tuple[str, ...]) -> Callable[[bytes], bool]:
    """Whether an audit row in COPY's text format is a project table's. A table name holds no tab or escape."""
    position = columns.index('table_name')

    def keeps_row(row: bytes) -> bool:
        return row.rstrip(b'\n').split(b'\t')[position].decode() in PROJECT_TABLES

    return keeps_row
