"""Jobs that run on the scheduler.

Jobs have to have the session created in this file,
since the session is not serializable and cannot be passed in as a parameter.
`SessionLocal` must be used instead of `get_sqlalchemy_session` because the generator produced
by the yield in `get_sqlalchemy_session` cannot be used as a context manager.
"""

import functools
import logging
from collections import defaultdict
from collections.abc import Callable
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pendulum
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from ichrisbirch import models
from ichrisbirch.config import Settings
from ichrisbirch.config import settings
from ichrisbirch.database.session import create_session
from ichrisbirch.scheduler.postgres_backup_restore import PostgresBackupRestore
from ichrisbirch.scheduler.postgres_snapshot_to_s3 import AwsRdsSnapshotS3
from ichrisbirch.util import find_project_root

logger = logging.getLogger(__name__)


daily_1am_trigger = CronTrigger(day='*', hour=1)
daily_115am_trigger = CronTrigger(day='*', hour=1, minute=15)
daily_130am_trigger = CronTrigger(day='*', hour=1, minute=30)
daily_3pm_trigger = CronTrigger(day='*', hour=15)


@dataclass
class JobToAdd:
    """Dataclass for packaging jobs to add to the scheduler This class is really only necessary to make main.py more clean in adding
    jobs.
    """

    func: Callable
    args: tuple
    trigger: Any
    id: str
    jobstore: str = 'ichrisbirch'
    replace_existing: bool = True

    def as_dict(self):
        return asdict(self)


def job_logger(func: Callable) -> Callable:
    """Decorator to log job start and completion."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f'started: {func.__name__}')
        start = pendulum.now()
        func(*args, **kwargs)
        elapsed = (pendulum.now() - start).in_words()
        logger.info(f'completed: {func.__name__} - {elapsed}')

    return wrapper


@job_logger
def make_logs(settings: Settings) -> None:
    logger.debug(f'time: {pendulum.now()}')
    logger.info(f'cwd: {Path.cwd()}')
    logger.info(f'project root: {find_project_root()}')
    logger.debug(f"environment: '{settings.ENVIRONMENT}'")
    logger.warning('this is a warning')
    logger.error('PAUSE this job to stop the logs')


@job_logger
def decrease_task_priority(settings: Settings) -> None:
    """Decrease priority of all tasks by 1."""
    with create_session(settings) as session:
        query = select(models.Task).filter(models.Task.complete_date.is_(None))
        for task in session.scalars(query).all():
            task.priority -= 1
        session.commit()


@job_logger
def check_and_run_autotasks(settings: Settings) -> None:
    """Check if any autotasks should run today and create tasks if not at max concurrent."""
    with create_session(settings) as session:
        tasks_count_by_name: dict[str, int] = defaultdict(int)
        for task in session.scalars(select(models.Task)).all():
            tasks_count_by_name[task.name] += 1
        for autotask in session.scalars(select(models.AutoTask)).all():
            if not autotask.should_run_today:
                continue
            concurrent = tasks_count_by_name.get(autotask.name, 0)
            logger.info(f'{autotask.name} concurrent tasks: {concurrent}')
            if concurrent >= autotask.max_concurrent:
                logger.info(f'skipping {autotask.name} with {concurrent} of max {autotask.max_concurrent}')
            else:
                session.add(
                    models.Task(
                        name=autotask.name,
                        category=autotask.category,
                        priority=autotask.priority,
                        notes=autotask.notes,
                    )
                )
                autotask.last_run_date = datetime.now()
                autotask.run_count += 1
        session.commit()


@job_logger
def aws_postgres_snapshot_to_s3():
    """Create a snapshot from RDS postgres and save it to S3, then delete the snapshot.

    This function is an alternative to the postgres_backup for testing but it is difficult to restore from a snapshot.
    """
    rds_snap = AwsRdsSnapshotS3(logger=logger, settings=settings)
    rds_snap.snapshot()


@job_logger
def postgres_backup(settings: Settings, logger: logging.Logger) -> None:
    pbr = PostgresBackupRestore(settings=settings, logger=logger)
    pbr.backup()


jobs_to_add = [
    JobToAdd(
        func=make_logs,
        args=(settings,),
        trigger=CronTrigger(second=15),
        id='make_logs',
    ),
    JobToAdd(
        func=decrease_task_priority,
        args=(settings,),
        trigger=daily_1am_trigger,
        id='decrease_task_priority_daily',
    ),
    JobToAdd(
        func=check_and_run_autotasks,
        args=(settings,),
        trigger=daily_115am_trigger,
        id='check_and_run_autotasks_daily',
    ),
    JobToAdd(
        func=postgres_backup,
        args=(settings, logger),
        trigger=daily_130am_trigger,
        id='postgres_backup_daily',
    ),
]
