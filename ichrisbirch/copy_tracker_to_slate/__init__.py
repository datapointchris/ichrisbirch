"""A one-time copy of icb's tracker into slate's database, proven table by table before it commits.

`python -m ichrisbirch.copy_tracker_to_slate --dump <file or directory> [--target <url>] [--rehearse]`
reads a plain `pg_dump` of icb's database, the format a nightly backup takes, and writes slate's
database in one transaction. Every initiative and issue keeps its number, and every comment, label,
dependency, live claim and history row carries over. `--rehearse` proves the copy and rolls it back.
"""
