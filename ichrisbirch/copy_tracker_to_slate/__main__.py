"""Copy icb's tracker from a dump into slate's database, and print the proof.

Exits 0 when every table is proven, whether committed or rolled back as a rehearsal, 1 when a proof
differs, and 2 when the copy stopped for any other reason. Nothing is committed unless it exits 0.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path

import psycopg
import structlog

from ichrisbirch.copy_tracker_to_slate.copy_refused import CopyRefused
from ichrisbirch.copy_tracker_to_slate.dumped_tracker import TRACKER_TABLES
from ichrisbirch.copy_tracker_to_slate.plain_pg_dump import DumpFile
from ichrisbirch.copy_tracker_to_slate.plain_pg_dump import PlainDump
from ichrisbirch.copy_tracker_to_slate.write_and_prove import CopyResult
from ichrisbirch.copy_tracker_to_slate.write_and_prove import write_and_prove

logger = structlog.get_logger()

# A pod's first connections to the cluster's Postgres are refused until its network policy admits it.
CONNECT_ATTEMPTS = 30
CONNECT_PAUSE_SECONDS = 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog='python -m ichrisbirch.copy_tracker_to_slate', description=__doc__)
    parser.add_argument('--dump', type=Path, required=True, help="a plain pg_dump of icb's database, or a directory whose newest is read")
    parser.add_argument('--target', default=os.environ.get('DATABASE_URL'), help="slate's database URL, by default DATABASE_URL")
    parser.add_argument('--rehearse', action='store_true', help='prove the copy, then roll it back')
    args = parser.parse_args(argv)
    if not args.target:
        parser.error("name slate's database with --target or DATABASE_URL")

    started = time.monotonic()
    try:
        dump_file = DumpFile.find(args.dump)
        print_dump_file(dump_file)
        with connect(args.target) as connection, dump_file.open() as stream:
            dump = PlainDump(stream)
            result = write_and_prove(connection, dump, rehearse=args.rehearse)
    except CopyRefused as refused:
        print(f'\nRefused, and nothing was written: {refused}')
        return 2
    except psycopg.Error as failed:
        print(f"\nslate's database failed the copy, and nothing was written: {type(failed).__name__}: {str(failed).strip()}")
        return 2
    print_result(dump, result, seconds=time.monotonic() - started)
    return 0 if result.proven else 1


def connect(url: str) -> psycopg.Connection:
    # The cluster hands a postgres:// URL. A SQLAlchemy URL names its driver, which libpq does not read.
    conninfo = re.sub(r'^postgresql\+\w+://', 'postgresql://', url)
    for attempt in range(1, CONNECT_ATTEMPTS + 1):
        try:
            return psycopg.connect(conninfo, application_name='copy_tracker_to_slate')
        except psycopg.OperationalError as refused:
            if attempt == CONNECT_ATTEMPTS:
                raise CopyRefused(f"slate's database refused {CONNECT_ATTEMPTS} connections, the last with: {refused}") from refused
            logger.warning('tracker_copy_connect_retry', attempt=attempt, error=str(refused).strip())
            time.sleep(CONNECT_PAUSE_SECONDS)
    raise AssertionError('unreachable')


def print_dump_file(dump_file: DumpFile) -> None:
    print(f'Dump  {dump_file.path}')
    print(f'      {dump_file.size_bytes:,} bytes, sha256 {dump_file.sha256}')


def print_result(dump: PlainDump, result: CopyResult, *, seconds: float) -> None:
    for version in dump.versions:
        print(f'      {version}')

    print(f'\n{"Read from the dump":<26}{"ROWS":>10}{"KEPT":>10}')
    for loaded in result.loaded.values():
        kept_note = f'  only the history of {len(TRACKER_TABLES)} tracker tables' if loaded.table == 'icb_audit_trail' else ''
        print(f'{loaded.table:<26}{loaded.rows_read:>10,}{loaded.rows_kept:>10,}{kept_note}')

    print(f'\n{"slate table":<26}{"ICB ROWS":>10}{"SLATE ROWS":>12}  {"ICB MD5":<34}{"SLATE MD5":<34}')
    for proof in result.proofs:
        verdict = 'match' if proof.matches else 'DIFFERS'
        print(f'{proof.table:<26}{proof.icb_rows:>10,}{proof.slate_rows:>12,}  {proof.icb_md5:<34}{proof.slate_md5:<34}{verdict}')
        for row in proof.only_in_icb:
            print(f'    only in icb:   {row}')
        for row in proof.only_in_slate:
            print(f'    only in slate: {row}')

    print(f"\nicb's item_numbers last gave {result.item_numbers.last_value}.")
    for restart in result.restarts:
        print(f'{restart.sequence} restarts at {restart.restarts_at:,}.')

    differing = sum(not proof.matches for proof in result.proofs)
    if differing:
        outcome = f'{differing} of {len(result.proofs)} tables differ, so nothing was committed'
    elif result.committed:
        outcome = 'Every table is proven, and the copy is committed'
    else:
        outcome = 'Every table is proven, and the copy is rolled back, because this is a rehearsal'
    print(f'\n{outcome}. {seconds:.1f}s.')


if __name__ == '__main__':
    sys.exit(main())
