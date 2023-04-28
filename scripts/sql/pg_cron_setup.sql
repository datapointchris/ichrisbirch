
CREATE EXTENSION pg_cron;





-- See jobs
SELECT * FROM cron.job;


-- See job runs
SELECT * FROM cron.job_run_details;
