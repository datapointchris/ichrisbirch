# pg_cron

Location: `/scripts/sql/pg_cron_setup.sql`

1. pg_cron must be added to 'shared_preload_libraries'
   1. Reboot required
2. pg_cron runs in the default postgres database, then jobs can be moved to specific databases
3. For AWS RDS: <https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/PostgreSQL_pg_cron.html>

## Basic Instructions

1. Create a function / procedure to run
2. Schedule it with a name
3. Set the database name for the job to the correct db
4. Check that the job details show it has run successfully

!!! note "Note"
    `pg_cron` is not being used anymore, in favor of `APScheduler` in the `ichrisbirch/scheduler` directory.
