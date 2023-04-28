-- Decrease priority by 1 function
CREATE OR REPLACE FUNCTION decrease_priority_daily()
RETURNS void AS $$
BEGIN
  UPDATE tasks
  SET priority = priority - 1
  WHERE priority > 1
  AND complete_date IS NULL;
END;
$$ LANGUAGE plpgsql;


-- Schedule the Function to run daily at 12:01am
SELECT cron.schedule('decrease_priority', '1 0 * * *', 'SELECT decrease_priority_daily();');


-- Move the job to the corresponding database
UPDATE cron.job
SET DATABASE = 'ichrisbirch'
WHERE jobid = (SELECT jobid from cron.job WHERE jobname = 'decrease_priority');
