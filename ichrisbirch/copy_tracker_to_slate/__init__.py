"""A one-time copy of icb's tracker into slate's database, proven table by table before it commits.

`python -m ichrisbirch.copy_tracker_to_slate {check,commit} --dump <file or directory> [--target <url>]`
reads a plain-format `pg_dump` of icb's database, gzipped or not, and writes slate's database in one
transaction. Every initiative and issue keeps its number. Every comment, label, dependency and current
claim carries over, and so does the history of the tracker's tables. `check` proves the copy and rolls
it back.
"""
