"""One pass over a plain-format `pg_dump`: the versions it names, its COPY blocks and its sequence values.

Each COPY block's rows stay in COPY's text format, so they load into another table with
`COPY ... FROM STDIN` unparsed.
"""

from __future__ import annotations

import dataclasses as dc
import gzip
import hashlib
import io
import re
import zlib
from collections.abc import Iterator
from pathlib import Path

from ichrisbirch.copy_projects_to_new_database.copy_refused import CopyRefused

COPY_START = re.compile(rb'^COPY public\.(?P<table>\w+) \((?P<columns>.*)\) FROM stdin;\n$')
COPY_END = b'\\.\n'
SEQUENCE_SET = re.compile(rb"^SELECT pg_catalog\.setval\('public\.(?P<sequence>\w+)', (?P<value>\d+), (?P<is_called>true|false)\);\n$")
VERSION_LINE = re.compile(rb'^-- (?P<line>Dumped (from database|by pg_dump) version .*)\n$')
# pg_dump writes this after everything else, so a dump without it was cut short.
DUMP_COMPLETE = b'-- PostgreSQL database dump complete\n'
GZIP_MAGIC = b'\x1f\x8b'
# A directory of backups holds other databases' dumps beside icb's, each named for its database and then dated.
DUMP_NAME_PREFIX = 'ichrisbirch-'


@dc.dataclass(frozen=True)
class DumpFile:
    path: Path
    size_bytes: int
    sha256: str

    @classmethod
    def find(cls, path: Path) -> DumpFile:
        """The dump at `path`, or in a directory the last by name of its `ichrisbirch-*.sql.gz` and `ichrisbirch-*.sql` files."""
        if path.is_dir():
            patterns = (f'{DUMP_NAME_PREFIX}*.sql.gz', f'{DUMP_NAME_PREFIX}*.sql')
            candidates = sorted([found for pattern in patterns for found in path.glob(pattern)], key=lambda found: found.name)
            if not candidates:
                raise CopyRefused(f'{path} holds no {" or ".join(patterns)} dump')
            path = candidates[-1]
        if not path.is_file():
            raise CopyRefused(f'{path} is not a file')
        content_hash = hashlib.sha256()
        try:
            with path.open('rb') as dump:
                while chunk := dump.read(1 << 20):
                    content_hash.update(chunk)
        except OSError as unreadable:
            raise CopyRefused(f'{path} could not be read: {unreadable}') from unreadable
        return cls(path=path, size_bytes=path.stat().st_size, sha256=content_hash.hexdigest())

    def open(self) -> io.BufferedIOBase:
        with self.path.open('rb') as probe:
            compressed = probe.read(2) == GZIP_MAGIC
        return gzip.open(self.path, 'rb') if compressed else self.path.open('rb')


@dc.dataclass(frozen=True)
class SequenceValue:
    last_value: int
    is_called: bool

    @property
    def next_value(self) -> int:
        return self.last_value + 1 if self.is_called else self.last_value


@dc.dataclass
class CopyBlock:
    table: str
    columns: tuple[str, ...]
    lines: Iterator[bytes]
    rows_read: int = 0
    ended: bool = False

    def rows(self) -> Iterator[bytes]:
        """Each data line, newline included, until the block's terminator."""
        for line in self.lines:
            if line == COPY_END:
                self.ended = True
                return
            self.rows_read += 1
            yield line
        raise CopyRefused(f'the dump ends inside the COPY block of {self.table}')

    def skip(self) -> None:
        if not self.ended:
            for _ in self.rows():
                pass


@dc.dataclass
class PlainDump:
    stream: io.BufferedIOBase
    versions: list[str] = dc.field(default_factory=list)
    # Filled as the pass reaches them, and pg_dump writes them after every COPY block.
    sequences: dict[str, SequenceValue] = dc.field(default_factory=dict)
    complete: bool = False

    def copy_blocks(self) -> Iterator[CopyBlock]:
        """Every COPY block in order. Rows a caller leaves unread are skipped before the next block."""
        lines = read_lines(self.stream)
        for line in lines:
            if line == DUMP_COMPLETE:
                self.complete = True
            elif start := COPY_START.match(line):
                block = CopyBlock(start['table'].decode(), column_names(start['columns'].decode()), lines)
                yield block
                block.skip()
            elif setting := SEQUENCE_SET.match(line):
                self.sequences[setting['sequence'].decode()] = SequenceValue(int(setting['value']), setting['is_called'] == b'true')
            elif version := VERSION_LINE.match(line):
                self.versions.append(version['line'].decode())


def read_lines(stream: io.BufferedIOBase) -> Iterator[bytes]:
    try:
        yield from stream
    except (OSError, EOFError, zlib.error) as unreadable:
        raise CopyRefused(f'the dump could not be read to its end: {type(unreadable).__name__}: {unreadable}') from unreadable


def column_names(listed: str) -> tuple[str, ...]:
    """The names in a COPY header's column list, unquoted. pg_dump quotes a name that is a keyword, such as "position"."""
    return tuple(name[1:-1].replace('""', '"') if name.startswith('"') else name for name in listed.split(', '))
