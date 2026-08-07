"""Import the dotfiles `patterns` JSONL store into the patterns API.

The dotfiles tool wrote `~/.local/share/patterns/entries.jsonl`, which was in
neither Syncthing nor git — so entries are stranded on whichever machine wrote
them and this file is the only copy. Run this once per machine that has one,
after the patterns endpoint is deployed.

Goes through `icb` rather than the database, so it targets whatever environment
`icb` is authenticated against and takes the same path any other write does.

    uv run python scripts/import_dotfiles_patterns.py --dry-run
    uv run python scripts/import_dotfiles_patterns.py

Re-running is safe: an entry whose message and timestamp already exist is
skipped, because the store has no ids to deduplicate on.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_STORE = Path.home() / '.local' / 'share' / 'patterns' / 'entries.jsonl'


def read_entries(store: Path) -> list[dict]:
    """Parse the store, which is concatenated pretty-printed JSON objects rather than true JSONL."""
    decoder = json.JSONDecoder()
    text = store.read_text().strip()
    entries = []
    index = 0
    while index < len(text):
        entry, offset = decoder.raw_decode(text, index)
        entries.append(entry)
        index = offset
        while index < len(text) and text[index] in ' \t\r\n':
            index += 1
    return entries


def normalize_timestamp(raw: str) -> str:
    """The store writes %z without a colon ('-0500'); RFC3339 wants one."""
    return datetime.strptime(raw, '%Y-%m-%dT%H:%M:%S%z').isoformat()


def instant(raw: str) -> datetime:
    """A timestamp as a comparable instant.

    The API answers in UTC while the store records a local offset, so comparing
    the strings makes every entry look new and a second run duplicates all of
    them. Parsing both to aware datetimes is what makes re-running safe.
    """
    return datetime.fromisoformat(raw.replace('Z', '+00:00')).replace(microsecond=0)


def existing_keys() -> set[tuple[str, datetime]]:
    result = subprocess.run(['icb', 'patterns', 'list', '--json'], capture_output=True, text=True, check=True)
    return {(p['message'], instant(p['recorded_at'])) for p in json.loads(result.stdout or '[]')}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store', type=Path, default=DEFAULT_STORE, help=f'JSONL store (default: {DEFAULT_STORE})')
    parser.add_argument('--dry-run', action='store_true', help='Report what would be imported, write nothing')
    args = parser.parse_args()

    if not args.store.exists():
        print(f'no store at {args.store} — nothing to import')
        return 0

    entries = read_entries(args.store)
    print(f'{len(entries)} entries in {args.store}')

    already = set() if args.dry_run else existing_keys()

    imported = skipped = 0
    for entry in entries:
        recorded_at = normalize_timestamp(entry['timestamp'])
        if (entry['message'], instant(recorded_at)) in already:
            skipped += 1
            continue
        if args.dry_run:
            print(f'  would import  {recorded_at}  {entry["message"][:70]}')
            imported += 1
            continue
        subprocess.run(
            ['icb', 'patterns', 'create', entry['message'], '--at', recorded_at],
            check=True,
            capture_output=True,
        )
        imported += 1

    verb = 'would import' if args.dry_run else 'imported'
    print(f'{verb} {imported}, skipped {skipped} already present')
    return 0


if __name__ == '__main__':
    sys.exit(main())
