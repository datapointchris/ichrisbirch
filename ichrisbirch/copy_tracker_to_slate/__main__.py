"""Copy icb's tracker from a dump into slate's database, and print the proof.

`check` copies and proves, then rolls back. `commit` copies and proves, and commits only when every
table is proven. Each exit code means one outcome:

  0  every table is proven, and `commit` committed the copy while `check` rolled it back
  1  a proof differs, and nothing was committed
  2  the command line is wrong
  3  the copy refused the dump or slate's database as they stand, and nothing was written
  4  slate's database gave no answer in time, and nothing was written: no connection in 60
     seconds, a lock held past 30, or a connection lost midway. A later run can succeed.
"""

from __future__ import annotations

import argparse
import math
import os
import re
import sys
import time
import traceback
from pathlib import Path

import psycopg
import structlog

from ichrisbirch.copy_tracker_to_slate.copy_refused import CopyRefused
from ichrisbirch.copy_tracker_to_slate.dumped_tracker import TRACKER_TABLES
from ichrisbirch.copy_tracker_to_slate.plain_pg_dump import DUMP_NAME_PREFIX
from ichrisbirch.copy_tracker_to_slate.plain_pg_dump import DumpFile
from ichrisbirch.copy_tracker_to_slate.plain_pg_dump import PlainDump
from ichrisbirch.copy_tracker_to_slate.write_and_prove import CopyResult
from ichrisbirch.copy_tracker_to_slate.write_and_prove import write_and_prove

logger = structlog.get_logger()

# A network policy may admit a new pod's traffic only after it starts, refusing its first connections.
CONNECT_DEADLINE_SECONDS = 60
CONNECT_RETRY_SECONDS = 1

EXIT_PROVEN = 0
EXIT_PROOF_DIFFERS = 1
EXIT_REFUSED = 3
EXIT_NO_ANSWER = 4


class SlateGaveNoAnswer(Exception):
    """slate's database gave no answer in time, so the same run may succeed later."""


def main(argv: list[str] | None = None) -> int:
    args = parse_arguments(argv)
    started = time.monotonic()
    try:
        dump_file = DumpFile.find(args.dump)
        print_dump_file(dump_file)
        with connect(args.target) as connection, dump_file.open() as stream:
            dump = PlainDump(stream)
            result = write_and_prove(connection, dump, commit=args.verb == 'commit')
    except CopyRefused as refused:
        print(f'\nRefused, and nothing was written: {refused}')
        return EXIT_REFUSED
    except SlateGaveNoAnswer as unanswered:
        print(f'\n{unanswered}')
        return EXIT_NO_ANSWER
    except psycopg.errors.LockNotAvailable as locked:
        print(f"\nslate's tables stayed locked past the copy's lock timeout, and nothing was written: {str(locked).strip()}")
        return EXIT_NO_ANSWER
    except psycopg.Error as failed:
        # A server that answered gives its error a SQLSTATE. A connection lost midway has none.
        if isinstance(failed, psycopg.OperationalError) and failed.sqlstate is None:
            print(f"\nslate's database stopped answering, and nothing was written: {str(failed).strip()}")
            return EXIT_NO_ANSWER
        print(f"\nslate's database failed the copy, and nothing was written: {type(failed).__name__}: {str(failed).strip()}")
        return EXIT_REFUSED
    except Exception:
        traceback.print_exc()
        print('\nStopped by an unexpected error, and nothing was written.')
        return EXIT_REFUSED
    print_result(dump, result, seconds=time.monotonic() - started)
    return EXIT_PROVEN if result.proven else EXIT_PROOF_DIFFERS


def parse_arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog='python -m ichrisbirch.copy_tracker_to_slate', description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    verbs = parser.add_subparsers(dest='verb', required=True)
    for verb, summary in (
        ('check', 'copy and prove, then roll back, leaving slate as it was'),
        ('commit', 'copy and prove, and commit only when every table is proven'),
    ):
        command = verbs.add_parser(verb, help=summary, description=summary)
        command.add_argument(
            '--dump',
            type=Path,
            required=True,
            help=f"a plain pg_dump of icb's database, or a directory whose last {DUMP_NAME_PREFIX}*.sql.gz or *.sql by name is read",
        )
        command.add_argument('--target', default=os.environ.get('DATABASE_URL'), help="slate's database URL, by default DATABASE_URL")
    args = parser.parse_args(argv)
    if not args.target:
        parser.error("name slate's database with --target or DATABASE_URL")
    return args


def connect(url: str) -> psycopg.Connection:
    # The cluster hands a postgres:// URL. A SQLAlchemy URL names its driver, which libpq does not read.
    conninfo = re.sub(r'^postgresql\+\w+://', 'postgresql://', url)
    deadline = time.monotonic() + CONNECT_DEADLINE_SECONDS
    while True:
        # libpq waits at least two seconds for an attempt, whatever it is given.
        attempt_seconds = max(2, math.ceil(deadline - time.monotonic()))
        try:
            return psycopg.connect(conninfo, application_name='copy_tracker_to_slate', connect_timeout=attempt_seconds)
        except psycopg.OperationalError as failed:
            if time.monotonic() + CONNECT_RETRY_SECONDS >= deadline:
                raise never_connected(failed) from failed
            logger.warning('tracker_copy_connect_retry', error=str(failed).strip())
            time.sleep(CONNECT_RETRY_SECONDS)


def never_connected(failed: psycopg.OperationalError) -> Exception:
    """libpq gives a failed connection no SQLSTATE. It reports a refusal the server itself sent as FATAL."""
    last = str(failed).strip()
    if 'FATAL:' in last:
        return CopyRefused(f"slate's database refused every connection for {CONNECT_DEADLINE_SECONDS}s, the last with: {last}")
    return SlateGaveNoAnswer(
        f"slate's database gave no connection in {CONNECT_DEADLINE_SECONDS}s, and nothing was written. The last attempt failed with: {last}"
    )


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

    print(f'\n{"slate table":<26}{"COLUMNS":<12}{"ICB ROWS":>10}{"SLATE ROWS":>12}  {"ICB MD5":<34}{"SLATE MD5":<34}')
    for proof in result.proofs:
        verdict = 'match' if proof.matches else 'DIFFERS'
        print(
            f'{proof.table:<26}{proof.columns:<12}{proof.icb_rows:>10,}{proof.slate_rows:>12,}  '
            f'{proof.icb_md5:<34}{proof.slate_md5:<34}{verdict}'
        )
        for row in proof.only_in_icb:
            print(f'    only in icb:   {row}')
        for row in proof.only_in_slate:
            print(f'    only in slate: {row}')

    print(f"\nicb's item_numbers last gave {result.item_numbers.last_value}.")
    for restart in result.restarts:
        print(f'{restart.sequence} restarts at {restart.restarts_at:,}.')

    differing = sum(not proof.matches for proof in result.proofs)
    if differing:
        outcome = f'{differing} of {len(result.proofs)} proofs differ, so nothing was committed'
    elif result.committed:
        outcome = 'Every table is proven, and the copy is committed'
    else:
        outcome = 'Every table is proven, and the copy is rolled back, because check never commits'
    print(f'\n{outcome}. {seconds:.1f}s.')


if __name__ == '__main__':
    sys.exit(main())
