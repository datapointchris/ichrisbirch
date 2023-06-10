from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from ichrisbirch.database.sqlalchemy.base import Base
from ichrisbirch.scheduler import jobs
from ichrisbirch.config import get_settings

settings = get_settings()


def create_scheduler() -> BackgroundScheduler:
    """Create the scheduler

    Start after the app and api are created to avoid any conflicts
    """
    jobstore = SQLAlchemyJobStore(url=settings.sqlalchemy.db_uri, metadata=Base.metadata)
    daily_1am_trigger = CronTrigger(day='*', hour=1)

    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_jobstore(jobstore, alias='ichrisbirch', extend_existing=True)

    scheduler.add_job(
        jobs.decrease_task_priority,
        trigger=daily_1am_trigger,
        id='daily_decrease_task_priority',
        jobstore='ichrisbirch',
        replace_existing=True,
    )
    scheduler.add_job(
        jobs.check_and_run_autotasks,
        trigger=daily_1am_trigger,
        id='check_for_autotasks_to_run',
        jobstore='ichrisbirch',
        replace_existing=True,
    )
    scheduler.start()
    return scheduler
