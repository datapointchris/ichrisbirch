"""The copy as one transaction on the projects database: refuse, load, write, prove, then commit or roll back.

Nothing is committed unless every proof matches. `check` rolls back a proven copy too, and leaves
nothing behind, because each sequence moves with `RESTART`, which rolls back with the transaction.

The audit trigger is silenced per table with `DISABLE TRIGGER` rather than `session_replication_role =
replica`. Only a superuser may set that, and it would also stop foreign keys being checked.
`DISABLE TRIGGER` needs the role that owns the tables, and so does each `RESTART`.
"""

from __future__ import annotations

import dataclasses as dc
from typing import Any

import psycopg
import structlog
from psycopg import sql

from ichrisbirch.copy_projects_to_new_database.copy_refused import CopyRefused
from ichrisbirch.copy_projects_to_new_database.dumped_icb_tables import DUMPED_BY_NAME
from ichrisbirch.copy_projects_to_new_database.dumped_icb_tables import LoadedRows
from ichrisbirch.copy_projects_to_new_database.dumped_icb_tables import load_dumped_projects
from ichrisbirch.copy_projects_to_new_database.plain_pg_dump import PlainDump
from ichrisbirch.copy_projects_to_new_database.plain_pg_dump import SequenceValue
from ichrisbirch.copy_projects_to_new_database.target_tables import COPIED_TABLES
from ichrisbirch.copy_projects_to_new_database.target_tables import HOLDING_PROJECT_ROWS
from ichrisbirch.copy_projects_to_new_database.target_tables import TARGET_TABLES
from ichrisbirch.copy_projects_to_new_database.target_tables import TargetTable
from ichrisbirch.copy_projects_to_new_database.target_tables import quoted

logger = structlog.get_logger()

# A count and an md5 over each row's own md5, sorted, so the sum reads the same in any row order. A
# row's text form carries its values and none of its column names.
CHECKSUM = (
    "SELECT count(*), md5(coalesce(string_agg(md5(row_text), '' ORDER BY md5(row_text)), '')) "
    'FROM (SELECT projected::text AS row_text FROM ({rows}) AS projected) AS hashed'
)
DIFFERING_ROWS_SHOWN = 5


@dc.dataclass(frozen=True)
class TableProof:
    table: str
    # `all` for the comparison through the copy's own mapping, `N by name` for the columns kept as they were.
    columns: str
    icb_rows: int
    icb_md5: str
    target_rows: int
    target_md5: str
    only_in_icb: tuple[tuple[Any, ...], ...] = ()
    only_in_target: tuple[tuple[Any, ...], ...] = ()

    @property
    def matches(self) -> bool:
        return self.icb_rows == self.target_rows and self.icb_md5 == self.target_md5


@dc.dataclass(frozen=True)
class SequenceRestart:
    sequence: str
    restarts_at: int


@dc.dataclass
class CopyResult:
    loaded: dict[str, LoadedRows]
    written: dict[str, int]
    item_numbers: SequenceValue
    proofs: list[TableProof]
    restarts: list[SequenceRestart]
    committed: bool

    @property
    def proven(self) -> bool:
        return all(proof.matches for proof in self.proofs)


def write_and_prove(connection: psycopg.Connection, dump: PlainDump, *, commit: bool) -> CopyResult:
    """Run the whole copy in the connection's transaction, which this commits only when asked to and proven."""
    try:
        result = write_and_prove_in_transaction(connection.cursor(), dump)
        if result.proven and commit:
            connection.commit()
            result.committed = True
        else:
            connection.rollback()
        return result
    except BaseException:
        connection.rollback()
        raise


def write_and_prove_in_transaction(cursor: psycopg.Cursor, dump: PlainDump) -> CopyResult:
    cursor.execute("SET LOCAL lock_timeout = '30s'")
    cursor.execute("SET LOCAL TimeZone = 'UTC'")
    cursor.execute(sql.SQL('LOCK TABLE {} IN EXCLUSIVE MODE').format(sql.SQL(', ').join(sql.Identifier(t.name) for t in TARGET_TABLES)))
    refuse_schema_this_copy_was_not_written_for(cursor)
    refuse_unless_empty(cursor)
    audit_baseline = scalar(cursor, 'SELECT coalesce(max(id), 0) FROM audit_trail')
    params = {'audit_baseline': audit_baseline}

    logger.info('projects_copy_loading_dump')
    loaded = load_dumped_projects(cursor, dump)
    item_numbers = dump.sequences.get('item_numbers')
    if item_numbers is None:
        raise CopyRefused("the dump sets no value for icb's item_numbers sequence")
    refuse_dropped_rows(cursor, params)

    logger.info('projects_copy_writing', tables=[table.name for table in TARGET_TABLES])
    for table in COPIED_TABLES:
        cursor.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER audit_trail').format(sql.Identifier(table.name)))
    written = {table.name: insert(cursor, table, params) for table in TARGET_TABLES}
    for table in COPIED_TABLES:
        cursor.execute(sql.SQL('ALTER TABLE {} ENABLE TRIGGER audit_trail').format(sql.Identifier(table.name)))

    logger.info('projects_copy_proving')
    proofs = [proof for table in TARGET_TABLES for proof in prove(cursor, table, params)]
    restarts = restart_sequences(cursor, item_numbers)
    return CopyResult(loaded=loaded, written=written, item_numbers=item_numbers, proofs=proofs, restarts=restarts, committed=False)


def scalar(cursor: psycopg.Cursor, query: str | sql.Composed, params: dict[str, Any] | None = None) -> Any:
    row = cursor.execute(query, params).fetchone()
    return row[0] if row else None


def refuse_schema_this_copy_was_not_written_for(cursor: psycopg.Cursor) -> None:
    """The catalog must hold each table's columns exactly, or a new column would take its default unproven."""
    differences = []
    for table in TARGET_TABLES:
        held = {
            name
            for (name,) in cursor.execute(
                'SELECT attname FROM pg_attribute WHERE attrelid = %s::regclass AND attnum > 0 AND NOT attisdropped', (table.name,)
            )
        }
        if unwritten := sorted(held - set(table.columns)):
            differences.append(f'{table.name} holds {", ".join(unwritten)}, which the copy writes nothing to')
        if absent := sorted(set(table.columns) - held):
            differences.append(f'{table.name} lacks {", ".join(absent)}, which the copy writes')
    if differences:
        raise CopyRefused(f"the target's schema is not the one this copy was written for: {'; '.join(differences)}")


def refuse_unless_empty(cursor: psycopg.Cursor) -> None:
    """A second commit would double every row, so a target already holding project rows is refused."""
    held = {
        table.name: count
        for table in HOLDING_PROJECT_ROWS
        if (count := scalar(cursor, sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(table.name))))
    }
    if held:
        raise CopyRefused(f'the target already holds project rows: {", ".join(f"{name} {count}" for name, count in held.items())}')


def refuse_dropped_rows(cursor: psycopg.Cursor, params: dict[str, Any]) -> None:
    dropped = []
    for table in TARGET_TABLES:
        projected = scalar(cursor, f'SELECT count(*) FROM {table.projection}', params)
        carried = scalar(cursor, table.carries)
        if projected != carried:
            dropped.append(f'{table.name} projects {projected} of the {carried} dumped rows it carries')
    if dropped:
        raise CopyRefused('; '.join(dropped))


def insert(cursor: psycopg.Cursor, table: TargetTable, params: dict[str, Any]) -> int:
    """The rows the insert wrote, which for a lookup leaves out each one the database already held."""
    try:
        cursor.execute(table.insert, params)
    except psycopg.errors.IntegrityError as refused:
        diagnostic = refused.diag
        raise CopyRefused(
            f'the target refused icb rows for {table.name}: {diagnostic.message_primary}'
            f'{f"; {diagnostic.message_detail}" if diagnostic.message_detail else ""}'
        ) from refused
    return cursor.rowcount


def next_value(cursor: psycopg.Cursor, sequence: sql.Composable) -> int:
    last_value, is_called = cursor.execute(sql.SQL('SELECT last_value, is_called FROM {}').format(sequence)).fetchone() or (0, False)
    return SequenceValue(last_value, is_called).next_value


def restart_sequences(cursor: psycopg.Cursor, item_numbers: SequenceValue) -> list[SequenceRestart]:
    """Item numbers continue after icb's counter, never after the highest copied, since icb gave numbers no row kept.

    Each sequence also stays past any value the target gave itself, which its own audit rows may name.
    """
    highest_copied = scalar(cursor, 'SELECT coalesce(max(number), 0) FROM project_items')
    if item_numbers.next_value <= highest_copied:
        raise CopyRefused(f"icb's item_numbers would next give {item_numbers.next_value}, which a copied item already holds")
    next_number = max(item_numbers.next_value, next_value(cursor, sql.Identifier('item_numbers')))
    cursor.execute(sql.SQL('ALTER SEQUENCE item_numbers RESTART WITH {}').format(sql.Literal(next_number)))

    identity = scalar(cursor, "SELECT pg_get_serial_sequence('audit_trail', 'id')")
    next_id = max(
        scalar(cursor, 'SELECT coalesce(max(id), 0) + 1 FROM audit_trail'),
        next_value(cursor, sql.SQL(identity)),
    )
    cursor.execute(sql.SQL('ALTER TABLE audit_trail ALTER COLUMN id RESTART WITH {}').format(sql.Literal(next_id)))
    return [SequenceRestart('item_numbers', next_number), SequenceRestart('audit_trail.id', next_id)]


def prove(cursor: psycopg.Cursor, table: TargetTable, params: dict[str, Any]) -> list[TableProof]:
    """The table through the copy's own mapping, then the columns it keeps from its counterpart, read from both sides."""
    proofs = [compare(cursor, table.name, 'all', table.source, table.target, params)]
    if table.counterpart is not None:
        counterpart = DUMPED_BY_NAME[table.counterpart]
        kept = quoted(table.kept_by_name(counterpart.columns))
        icb_rows = f'SELECT {kept} FROM {counterpart.loaded_as}'
        target_rows = f'SELECT {kept} FROM {table.name} {table.target_filter}'
        proofs.append(compare(cursor, table.name, f'{len(table.kept_by_name(counterpart.columns))} by name', icb_rows, target_rows, params))
    return proofs


def compare(cursor: psycopg.Cursor, table: str, columns: str, icb_rows: str, target_rows: str, params: dict[str, Any]) -> TableProof:
    icb_count, icb_md5 = cursor.execute(CHECKSUM.format(rows=icb_rows), params).fetchone() or (0, '')
    target_count, target_md5 = cursor.execute(CHECKSUM.format(rows=target_rows), params).fetchone() or (0, '')
    proof = TableProof(table, columns, icb_count, icb_md5, target_count, target_md5)
    if proof.matches:
        return proof
    return dc.replace(
        proof,
        only_in_icb=differing(cursor, icb_rows, target_rows, params),
        only_in_target=differing(cursor, target_rows, icb_rows, params),
    )


def differing(cursor: psycopg.Cursor, rows: str, against: str, params: dict[str, Any]) -> tuple[tuple[Any, ...], ...]:
    query = f'SELECT * FROM (({rows}) EXCEPT ALL ({against})) AS differing LIMIT {DIFFERING_ROWS_SHOWN}'
    return tuple(cursor.execute(query, params).fetchall())
