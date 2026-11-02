"""icb's tracker rows as a dump holds them, loaded into tables that live only for the copy's transaction.

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

from ichrisbirch.copy_tracker_to_slate.copy_refused import CopyRefused
from ichrisbirch.copy_tracker_to_slate.plain_pg_dump import PlainDump
from ichrisbirch.database.base import Base
from ichrisbirch.models.issue import Initiative
from ichrisbirch.models.issue import Issue
from ichrisbirch.models.issue import IssueComment
from ichrisbirch.models.issue import IssueDependency
from ichrisbirch.models.issue import IssueLabel
from ichrisbirch.models.issue import IssueLabelAssignment
from ichrisbirch.models.record_change import RecordChange

# Every table of icb's tracker, lookups included. Their rows in icb's audit trail are the history the copy carries.
TRACKER_TABLES = frozenset(
    {
        'initiative_statuses',
        'initiatives',
        'issue_comments',
        'issue_dependencies',
        'issue_label_assignments',
        'issue_labels',
        'issue_statuses',
        'issue_types',
        'issues',
    }
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
    DumpedTable(
        'initiatives',
        Initiative,
        ('id', 'number', 'name', 'description', 'status', 'status_reason', 'priority', 'position', 'autofix', 'created_ts', 'closed_ts'),
    ),
    DumpedTable(
        'issues',
        Issue,
        (
            'id',
            'number',
            'title',
            'description',
            'acceptance',
            'repo',
            'type',
            'status',
            'status_reason',
            'priority',
            'rank',
            'deferred_until_date',
            'claimed_by',
            'claim_expires_ts',
            'autofix',
            'initiative_id',
            'parent_id',
            'discovered_from_id',
            'duplicate_of_id',
            'created_ts',
            'updated_ts',
            'closed_ts',
            'closed_by',
        ),
    ),
    DumpedTable('issue_dependencies', IssueDependency, ('issue_id', 'depends_on_id')),
    DumpedTable('issue_labels', IssueLabel, ('id', 'slug', 'group_slug', 'description')),
    DumpedTable('issue_label_assignments', IssueLabelAssignment, ('issue_id', 'label_id')),
    DumpedTable('issue_comments', IssueComment, ('id', 'issue_id', 'body', 'author', 'created_ts')),
    # Every app's history shares this table, so only the tracker tables' rows are kept.
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


def load_dumped_tracker(cursor: psycopg.Cursor, dump: PlainDump) -> dict[str, LoadedRows]:
    """Load every tracker row the dump holds, and read past every other table's rows without sending them anywhere."""
    for table in DUMPED_TABLES:
        cursor.execute(table.create_statement())
    loaded: dict[str, LoadedRows] = {}
    for block in dump.copy_blocks():
        dumped = DUMPED_BY_NAME.get(block.table)
        if dumped is None:
            continue
        dumped.refuse_other_columns(block.columns)
        keeps_row = tracker_history_filter(block.columns) if dumped.name == 'icb_audit_trail' else None
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


def tracker_history_filter(columns: tuple[str, ...]) -> Callable[[bytes], bool]:
    """Whether an audit row in COPY's text format is a tracker table's. A table name holds no tab or escape."""
    position = columns.index('table_name')

    def keeps_row(row: bytes) -> bool:
        return row.rstrip(b'\n').split(b'\t')[position].decode() in TRACKER_TABLES

    return keeps_row
