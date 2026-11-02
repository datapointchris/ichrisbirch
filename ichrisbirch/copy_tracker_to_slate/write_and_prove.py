"""The copy as one transaction on slate's database: refuse, load, write, prove, then commit or roll back.

Nothing is committed unless every proof matches. `check` rolls back a proven copy too, and leaves
nothing behind, because each sequence moves with `RESTART`, which rolls back with the transaction.

The audit trigger is silenced per table with `DISABLE TRIGGER` rather than `session_replication_role =
replica`. Only a superuser may set that, and it would also stop foreign keys being checked.

Every write to an audited slate table waits for the copy, because each writes `audit_trail`, which
the copy locks from its first statement. Reads wait only from the sequence restarts, which come last.
"""

from __future__ import annotations

import dataclasses as dc
from collections.abc import Iterable
from typing import Any

import psycopg
import structlog
from psycopg import sql

from ichrisbirch.copy_tracker_to_slate.copy_refused import CopyRefused
from ichrisbirch.copy_tracker_to_slate.dumped_tracker import DUMPED_BY_NAME
from ichrisbirch.copy_tracker_to_slate.dumped_tracker import LoadedRows
from ichrisbirch.copy_tracker_to_slate.dumped_tracker import load_dumped_tracker
from ichrisbirch.copy_tracker_to_slate.plain_pg_dump import PlainDump
from ichrisbirch.copy_tracker_to_slate.plain_pg_dump import SequenceValue
from ichrisbirch.copy_tracker_to_slate.slate_tables import AUDIT_TRAIL
from ichrisbirch.copy_tracker_to_slate.slate_tables import AUDITED
from ichrisbirch.copy_tracker_to_slate.slate_tables import IDENTITY_COLUMNS
from ichrisbirch.copy_tracker_to_slate.slate_tables import SLATE_TABLES
from ichrisbirch.copy_tracker_to_slate.slate_tables import VOCABULARY
from ichrisbirch.copy_tracker_to_slate.slate_tables import SlateTable

logger = structlog.get_logger()

# A count and an md5 over each row's own md5, sorted, so the sum reads the same in any row order. A
# row's text form carries its values and none of its column names.
CHECKSUM = (
    "SELECT count(*), md5(coalesce(string_agg(md5(row_text), '' ORDER BY md5(row_text)), '')) "
    'FROM (SELECT projected::text AS row_text FROM ({rows}) AS projected) AS hashed'
)
DIFFERING_ROWS_SHOWN = 5
ROUTED_INITIATIVE_NAMES = frozenset({'progress'})


@dc.dataclass(frozen=True)
class TableProof:
    table: str
    # `all` for the comparison through the copy's own mapping, `N by name` for the columns kept as they were.
    columns: str
    icb_rows: int
    icb_md5: str
    slate_rows: int
    slate_md5: str
    only_in_icb: tuple[tuple[Any, ...], ...] = ()
    only_in_slate: tuple[tuple[Any, ...], ...] = ()

    @property
    def matches(self) -> bool:
        return self.icb_rows == self.slate_rows and self.icb_md5 == self.slate_md5


@dc.dataclass(frozen=True)
class SequenceRestart:
    sequence: str
    restarts_at: int


@dc.dataclass
class CopyResult:
    loaded: dict[str, LoadedRows]
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
    cursor.execute(sql.SQL('LOCK TABLE {} IN EXCLUSIVE MODE').format(sql.SQL(', ').join(sql.Identifier(t.name) for t in SLATE_TABLES)))
    refuse_unless_empty(cursor)
    refuse_schema_this_copy_was_not_written_for(cursor)
    audit_baseline = scalar(cursor, 'SELECT coalesce(max(id), 0) FROM audit_trail')
    params = {'audit_baseline': audit_baseline}

    logger.info('tracker_copy_loading_dump')
    loaded = load_dumped_tracker(cursor, dump)
    item_numbers = dump.sequences.get('item_numbers')
    if item_numbers is None:
        raise CopyRefused("the dump sets no value for icb's item_numbers sequence")
    refuse_unknown_vocabulary(cursor)
    refuse_initiative_names_slate_rejects(cursor)
    refuse_dropped_rows(cursor, params)

    logger.info('tracker_copy_writing', tables=[table.name for table in SLATE_TABLES])
    for name in AUDITED:
        cursor.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER audit_trail').format(sql.Identifier(name)))
    for table in SLATE_TABLES:
        insert(cursor, table, params)
    for name in AUDITED:
        cursor.execute(sql.SQL('ALTER TABLE {} ENABLE TRIGGER audit_trail').format(sql.Identifier(name)))

    logger.info('tracker_copy_proving')
    proofs = [proof for table in SLATE_TABLES for proof in prove(cursor, table, params)]
    restarts = restart_sequences(cursor, item_numbers, dump.sequences)
    return CopyResult(loaded=loaded, item_numbers=item_numbers, proofs=proofs, restarts=restarts, committed=False)


def scalar(cursor: psycopg.Cursor, query: str | sql.Composed, params: dict[str, Any] | None = None) -> Any:
    row = cursor.execute(query, params).fetchone()
    return row[0] if row else None


def refuse_unless_empty(cursor: psycopg.Cursor) -> None:
    """slate must hold none of the rows the copy writes. Its audit trail may hold its own history, which the copy follows."""
    held = {
        table.name: count
        for table in SLATE_TABLES
        if table is not AUDIT_TRAIL and (count := scalar(cursor, sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(table.name))))
    }
    if held:
        raise CopyRefused(f'slate already holds rows the copy would write: {", ".join(f"{name} {count}" for name, count in held.items())}')


def refuse_schema_this_copy_was_not_written_for(cursor: psycopg.Cursor) -> None:
    """slate's catalog must hold each table's columns exactly, or a new column would take its default unproven."""
    differences = []
    for table in SLATE_TABLES:
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
        raise CopyRefused(f"slate's schema is not the one this copy was written for: {'; '.join(differences)}")


def refuse_unknown_vocabulary(cursor: psycopg.Cursor) -> None:
    unknown = []
    for table, column, lookup in VOCABULARY:
        query = sql.SQL('SELECT DISTINCT {column} FROM {rows} WHERE {column} NOT IN (SELECT name FROM {lookup}) ORDER BY 1').format(
            column=sql.Identifier(column), rows=sql.SQL(table.projection), lookup=sql.Identifier(lookup)
        )
        unknown += [f'{table.name}.{column} {value!r}' for (value,) in cursor.execute(query)]
    if unknown:
        raise CopyRefused(f'icb uses values slate has no row for: {", ".join(unknown)}')


def refuse_initiative_names_slate_rejects(cursor: psycopg.Cursor) -> None:
    """slate's API refuses a name reading as `N` or `#N`, or one a route under /initiatives takes, and the copy writes past its API."""
    rejected = cursor.execute(
        """
        SELECT number, name, CASE WHEN name ~ '^#?[0-9]+$' THEN 'reads as a record number' ELSE 'is a path under /initiatives' END
        FROM dumped_initiatives WHERE name ~ '^#?[0-9]+$' OR name = ANY(%(routed)s) ORDER BY number
        """,
        {'routed': sorted(ROUTED_INITIATIVE_NAMES)},
    ).fetchall()
    if rejected:
        named = ', '.join(f'initiative {number} {name!r} {reason}' for number, name, reason in rejected)
        raise CopyRefused(f'slate refuses these initiative names: {named}')


def refuse_dropped_rows(cursor: psycopg.Cursor, params: dict[str, Any]) -> None:
    dropped = []
    for table in SLATE_TABLES:
        projected = scalar(cursor, f'SELECT count(*) FROM {table.projection}', params)
        carried = scalar(cursor, table.carries)
        if projected != carried:
            dropped.append(f'{table.name} projects {projected} of the {carried} dumped rows it carries')
    if dropped:
        raise CopyRefused('; '.join(dropped))


def insert(cursor: psycopg.Cursor, table: SlateTable, params: dict[str, Any]) -> None:
    try:
        cursor.execute(table.insert, params)
    except psycopg.errors.IntegrityError as refused:
        diagnostic = refused.diag
        raise CopyRefused(
            f'slate refused icb rows for {table.name}: {diagnostic.message_primary}'
            f'{f"; {diagnostic.message_detail}" if diagnostic.message_detail else ""}'
        ) from refused


def restart_sequences(
    cursor: psycopg.Cursor, item_numbers: SequenceValue, dumped_sequences: dict[str, SequenceValue]
) -> list[SequenceRestart]:
    """slate's numbers continue after icb's last, never after the highest copied, since icb's project items share it."""
    highest_copied = scalar(cursor, 'SELECT coalesce(max(number), 0) FROM records')
    if item_numbers.next_value <= highest_copied:
        raise CopyRefused(f"icb's item_numbers would next give {item_numbers.next_value}, which a copied record already holds")
    cursor.execute(sql.SQL('ALTER SEQUENCE record_numbers RESTART WITH {}').format(sql.Literal(item_numbers.next_value)))
    restarts = [SequenceRestart('record_numbers', item_numbers.next_value)]
    for name, icb_sequence in IDENTITY_COLUMNS:
        next_id = scalar(cursor, sql.SQL('SELECT coalesce(max(id), 0) + 1 FROM {}').format(sql.Identifier(name)))
        if icb_sequence is not None:
            if icb_sequence not in dumped_sequences:
                raise CopyRefused(f"the dump sets no value for icb's {icb_sequence}, which numbered the {name} ids the copy keeps")
            next_id = max(next_id, dumped_sequences[icb_sequence].next_value)
        cursor.execute(sql.SQL('ALTER TABLE {} ALTER COLUMN id RESTART WITH {}').format(sql.Identifier(name), sql.Literal(next_id)))
        restarts.append(SequenceRestart(f'{name}.id', next_id))
    return restarts


def prove(cursor: psycopg.Cursor, table: SlateTable, params: dict[str, Any]) -> list[TableProof]:
    """The table through the copy's own mapping, then the columns it keeps from its counterpart, read from both sides."""
    proofs = [compare(cursor, table.name, 'all', table.source, table.target, params)]
    if table.counterpart is not None:
        counterpart = DUMPED_BY_NAME[table.counterpart]
        kept = table.kept_by_name(counterpart.columns)
        icb_rows = f'SELECT {quoted(icb for _, icb in kept)} FROM {counterpart.loaded_as} {table.counterpart_filter}'
        slate_rows = f'SELECT {quoted(slate for slate, _ in kept)} FROM {table.name} {table.target_filter}'
        proofs.append(compare(cursor, table.name, f'{len(kept)} by name', icb_rows, slate_rows, params))
    return proofs


def quoted(names: Iterable[str]) -> str:
    return ', '.join(f'"{name}"' for name in names)


def compare(cursor: psycopg.Cursor, table: str, columns: str, icb_rows: str, slate_rows: str, params: dict[str, Any]) -> TableProof:
    icb_count, icb_md5 = cursor.execute(CHECKSUM.format(rows=icb_rows), params).fetchone() or (0, '')
    slate_count, slate_md5 = cursor.execute(CHECKSUM.format(rows=slate_rows), params).fetchone() or (0, '')
    proof = TableProof(table, columns, icb_count, icb_md5, slate_count, slate_md5)
    if proof.matches:
        return proof
    return dc.replace(
        proof,
        only_in_icb=differing(cursor, icb_rows, slate_rows, params),
        only_in_slate=differing(cursor, slate_rows, icb_rows, params),
    )


def differing(cursor: psycopg.Cursor, rows: str, against: str, params: dict[str, Any]) -> tuple[tuple[Any, ...], ...]:
    query = f'SELECT * FROM (({rows}) EXCEPT ALL ({against})) AS differing LIMIT {DIFFERING_ROWS_SHOWN}'
    return tuple(cursor.execute(query, params).fetchall())
