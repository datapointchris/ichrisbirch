# pg_cron

Location: `/scripts/config/pg_cron_setup.sql`

1. pg_cron must be added to 'shared_preload_libraries'
   1. Reboot required
2. pg_cron runs in the default postgres database, then jobs can be moved to specific databases
3. For AWS RDS: <https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/PostgreSQL_pg_cron.html>
4. `pg_cron_setup.sql`

TODO: [2023/03/29] - Add basic pg_cron instructions and what is running
