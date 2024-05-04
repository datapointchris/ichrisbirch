import logging

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.blocking import BlockingScheduler

from ichrisbirch.config import Settings
from ichrisbirch.database.sqlalchemy.base import Base
from ichrisbirch.scheduler.jobs import jobs_to_add

logger = logging.getLogger(__name__)


def create_scheduler(settings: Settings) -> BlockingScheduler:
    jobstore = SQLAlchemyJobStore(url=settings.sqlalchemy.db_uri, metadata=Base.metadata)
    scheduler = BlockingScheduler()
    scheduler.add_jobstore(jobstore, alias='ichrisbirch', extend_existing=True)
    for job in jobs_to_add:
        scheduler.add_job(**job.as_dict())

    try:
        logger.info('scheduler: started')
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        logger.info('scheduler: shutting down')
        scheduler.shutdown()
        logger.info('scheduler: shutdown')

    return scheduler
