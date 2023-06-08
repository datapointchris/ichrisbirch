from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import create_engine

from ichrisbirch.config import Settings


def create_scheduler(settings: Settings) -> BackgroundScheduler:
    """Create the scheduler

    This must be run after the app and api are created, since it uses the API for the jobs
    and if it isn't running yet, will get an endpoint error.
    """
    engine = create_engine(settings.sqlalchemy.db_uri, echo=settings.sqlalchemy.echo)
    jobstore = SQLAlchemyJobStore(engine=engine)
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_jobstore(jobstore, alias='ichrisbirch')
    return scheduler
