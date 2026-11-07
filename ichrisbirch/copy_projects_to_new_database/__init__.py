"""A one-time copy of icb's projects into the projects app's own database, proven table by table before it commits.

`python -m ichrisbirch.copy_projects_to_new_database {check,commit} --dump <file or directory> [--target <url>]`
reads a plain-format `pg_dump` of icb's database, gzipped or not, and writes the projects database in one
transaction. Every project, item, membership, dependency and task keeps its id, every item keeps its number,
and the history of the seven project tables comes with them. `check` proves the copy and rolls it back.
"""
