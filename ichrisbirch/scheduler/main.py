import logging

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.blocking import BlockingScheduler

from ichrisbirch.config import Settings
from ichrisbirch.scheduler.jobs import jobs_to_add

logger = logging.getLogger(__name__)


def get_jobstore(settings: Settings) -> SQLAlchemyJobStore:
    logger.info('Creating SQLAlchemy job store')
    jobstore = SQLAlchemyJobStore(url=settings.sqlalchemy.db_uri)
    logger.info(f'Job store created: {jobstore}')
    return jobstore


def create_scheduler(settings: Settings) -> BlockingScheduler:
    logger.info('initializing')
    scheduler = BlockingScheduler()
    logger.info(f'class: {scheduler.__class__.__name__}')
    jobstore = get_jobstore(settings)
    scheduler.add_jobstore(jobstore, alias=settings.sqlalchemy.database, extend_existing=True)
    logger.info(f'jobstore added to scheduler: {jobstore}')
    for job in jobs_to_add:
        j = scheduler.add_job(**job.as_dict())
        logger.info(f'job added: {job.id}')
        if j.id == 'make_logs':
            j.pause()
            logger.info(f'job paused: {j.id}')

    try:
        logger.info('scheduler starting')
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        logger.info('scheduler shutting down')
        scheduler.shutdown()
        logger.info('scheduler shutdown complete')

    return scheduler
