import logging

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from ichrisbirch.config import Settings
from ichrisbirch.database.sqlalchemy.base import Base
from ichrisbirch.scheduler import jobs

logger = logging.getLogger(__name__)


def create_scheduler(settings: Settings) -> BlockingScheduler:
    """Create the scheduler"""
    jobstore = SQLAlchemyJobStore(url=settings.sqlalchemy.db_uri, metadata=Base.metadata)
    daily_1am_trigger = CronTrigger(day='*', hour=1)

    scheduler = BlockingScheduler()
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

    try:
        logger.info('starting scheduler')
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        logger.info('shutting down scheduler')
        scheduler.shutdown()
        logger.info('scheduler shutdown')

    return scheduler
