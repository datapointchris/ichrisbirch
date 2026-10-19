# The icb audit trail

Every insert, update and delete to a row of any table leaves one entry in `icb_audit_trail`.
The entry names the table and the row's primary key. It holds each written column's old and new
value, and who wrote it. `GET /api/v1/admin/record-changes` reads it, filtered by table, row,
writer and time window.

## One table holds every write, so no entity needs its own history

A history table per entity would repeat the same columns in every one, and a new table would
start without one. The trail is filled by an `after_flush` listener on every SQLAlchemy session,
in `ichrisbirch/models/record_change.py`. A route, a scheduler job and a script are audited
without calling anything. A new table is audited from its first write.

The logs do not replace it. They are kept for a fixed retention period, and a log line or span
records that a request ran, never which values it changed. Each entry carries the `request_id` or
`job_run_id` of the write, which joins it to the logs while they last.

## Who wrote it comes from the request or the job

- **A person** is recorded by the user's email. `authenticated_user` binds it to the request's
  session.
- **A service client** is recorded by its client id. `get_scoped_client` binds it.
- **A scheduler job** is recorded as `scheduler/<job_name>`. The job wrapper binds `job_name` and
  `job_run_id` into structlog's context, and the listener reads them there.

A session with none of the three bound records no writer. A script run by hand is that case.

The `icb` CLI logs in as its user, so anything driving the CLI under that login is recorded as
that user. Only a service client is told apart from the person.

## A statement the unit of work never sees records itself

The listener reads the session's pending inserts, updates and deletes. A Core `update()` or
`delete()` executed directly bypasses them, so it calls `record_update(session, obj, values)`
before anything refreshes `obj`. The issue claims do this.

The rank renumbering in `services/fractional_rank.py` is not audited. It rewrites every row's rank
while keeping their order, so it changes nothing a reader would look for.

## A secret never reaches the trail

A column opts out with `info={'record_changes': False}`, and a table with the same key in its
`__table_args__` info. `users.password` opts out. So do `scheduler_job_runs`, which is itself a
record of what ran, and the trail itself.
