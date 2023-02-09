--------------------------------------------------
----- SETUP
--------------------------------------------------
CREATE EXTENSION pg_cron;



--------------------------------------------------
----- JOBS
--------------------------------------------------
/*
tasks.tasks
-- Update 'priority' field every week (7 days) after insertion
*/
SELECT
  cron.schedule('@daily',
  $$UPDATE tasks
SET
  priority = CASE
    WHEN priority - 10 < 1 THEN 1
ELSE priority - 10
  END
WHERE
  complete_date IS NULL
AND (
  SELECT
    -- Every 7 days
    EXTRACT(DAY FROM now() - add_date)::integer % 7 = 0)
AND (
  SELECT
    -- Except for first day
    EXTRACT(DAY FROM now() - add_date)::integer != 0)$$);



--------------------------------------------------
----- POST JOB CREATION
-- Move the job to the corresponding database
--------------------------------------------------
UPDATE
  cron.job
SET
  DATABASE = 'ichrisbirch'
WHERE
  jobid = 1;

-- See jobs
SELECT
  *
FROM
  cron.job;
