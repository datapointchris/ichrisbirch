import logging

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.blocking import BlockingScheduler

from ichrisbirch.config import Settings
from ichrisbirch.database.sqlalchemy.base import Base
from ichrisbirch.scheduler.jobs import jobs_to_add

logger = logging.getLogger('scheduler')


def create_scheduler(settings: Settings) -> BlockingScheduler:
    jobstore = SQLAlchemyJobStore(url=settings.sqlalchemy.db_uri, metadata=Base.metadata)
    logger.info(f'jobstore added: {jobstore}')
    scheduler = BlockingScheduler()
    logger.info(f'scheduler: {scheduler.__class__.__name__}')
    scheduler.add_jobstore(jobstore, alias='ichrisbirch', extend_existing=True)
    for job in jobs_to_add:
        scheduler.add_job(**job.as_dict())
        logger.info(f'job added: {job.id}')

    try:
        logger.info('scheduler starting')
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        logger.info('shutting down')
        scheduler.shutdown()
        logger.info('shutdown complete')

    return scheduler
