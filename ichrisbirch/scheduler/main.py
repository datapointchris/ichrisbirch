import structlog
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.blocking import BlockingScheduler

from ichrisbirch.config import Settings
from ichrisbirch.scheduler.jobs import get_jobs_to_add

logger = structlog.get_logger()


def get_jobstore(settings: Settings) -> SQLAlchemyJobStore:
    logger.info('jobstore_creating')
    jobstore = SQLAlchemyJobStore(url=settings.sqlalchemy.db_uri)
    logger.info('jobstore_created', jobstore=str(jobstore))
    return jobstore


def create_scheduler(settings: Settings) -> BlockingScheduler:
    logger.info('scheduler_initializing')
    scheduler = BlockingScheduler()
    logger.info('scheduler_type', class_name=scheduler.__class__.__name__)
    jobstore = get_jobstore(settings)
    scheduler.add_jobstore(jobstore, alias=settings.sqlalchemy.database, extend_existing=True)
    logger.info('jobstore_added', jobstore=str(jobstore))
    for job in get_jobs_to_add(settings):
        j = scheduler.add_job(**job.as_dict())
        logger.info('job_added', job_id=job.id)
        if j.id == 'make_logs':
            j.pause()
            logger.info('job_paused', job_id=j.id)

    try:
        logger.info('scheduler_starting')
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        logger.info('scheduler_shutting_down')
        scheduler.shutdown()
        logger.info('scheduler_shutdown_complete')

    return scheduler
