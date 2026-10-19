# The icb audit trail

Every insert, update and delete to a row of an icb table leaves one entry in `icb_audit_trail`.
The entry names the table and the row's primary key. It holds each written column's old and new
value, and who wrote it. `GET /api/v1/admin/record-changes` reads it, filtered by table, row,
writer and time window.

## A trigger on each table writes the entry, so no write path is missed

The function `icb_audit_trail_record()` runs after every row a table's trigger sees. That covers
the ORM, a Core `update()` or `delete()`, raw SQL, and an `ON DELETE SET NULL` or `CASCADE` that
Postgres applies itself. An application-side listener sees only what the ORM flushes, and a
foreign-key action changes rows the ORM never loaded.

A table's trigger is created in its migration. `test_every_table_is_audited_but_what_opts_out`
fails on a mapped table without one, and gives the statement to add.

The logs do not replace the trail. They are kept for a fixed retention period, and a log line or
span records that a request ran, never which values it changed. Each entry carries the
`request_id` or `job_run_id` of the write, which joins it to the logs while they last.

## Who wrote it comes from the session's transaction

The trigger reads three transaction-local settings: `icb.actor`, `icb.request_id` and
`icb.job_run_id`. An `after_begin` listener in `ichrisbirch/models/record_change.py` sets them
whenever a session begins a transaction, so they end with it.

- **A person** is recorded by the user's email. `authenticated_user` binds it to the request's
  session.
- **A service client** is recorded by its client id. `get_scoped_client` binds it.
- **A scheduler job** is recorded as `scheduler/<job_name>`. The job wrapper binds `job_name` and
  `job_run_id` into structlog's context, and the listener reads them there.
- **A bulk article import** is recorded by the user who queued it. The queue item carries the
  email and the request id, and the worker binds both.

A session with none of these bound records no writer.

The `icb` CLI logs in as its user, so anything driving the CLI under that login is recorded as
that user. Only a service client is told apart from the person.

## A secret column opts out of the trail

Every column is recorded unless it opts out. A column opts out with
`info={'record_changes': False}`, and its table's trigger names it as an argument, which the
trigger strips from the row. A table opts out with the same key in its `__table_args__` info and
has no trigger. `users.password` opts out. So do `scheduler_job_runs`, which is itself a record of
what ran, and the trail itself. The same test fails on a column named like a credential that has
not opted out.
