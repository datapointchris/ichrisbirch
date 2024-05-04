"""Jobs that run on the scheduler.

Jobs have to have the session created in this file,
since the session is not serializable and cannot be passed in as a parameter.
`SessionLocal` must be used instead of `get_sqlalchemy_session` because the generator produced
by the yield in `get_sqlalchemy_session` cannot be used as a context manager.

"""

import logging
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from typing import Callable

from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import and_
from sqlalchemy import select

from ichrisbirch import models
from ichrisbirch.database.sqlalchemy.session import SessionLocal

logger = logging.getLogger(__name__)


daily_1am_trigger = CronTrigger(day='*', hour=1)


@dataclass
class JobToAdd:
    """Dataclass for packaging jobs to add to the scheduler This class is really only necessary to make main.py more
    clean in adding jobs.
    """

    func: Callable
    trigger: Any
    id: str
    jobstore: str = 'ichrisbirch'
    replace_existing: bool = True

    def as_dict(self):
        return asdict(self)


def decrease_task_priority() -> None:
    """Decrease priority of all tasks by 1."""
    logger.info('scheduler: job started: task priority decrease')
    with SessionLocal() as session:
        query = select(models.Task).filter(and_(models.Task.priority > 1, models.Task.complete_date.is_(None)))
        for task in session.scalars(query).all():
            task.priority -= 1
        session.commit()
    logger.info('scheduler: job completed: task priority decrease')


def check_and_run_autotasks() -> None:
    """Check if any autotasks should run today and create tasks if so."""
    logger.info('scheduler: job started: autotask check and run')
    with SessionLocal() as session:
        for autotask in session.scalars(select(models.AutoTask)).all():
            if autotask.should_run_today:
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
    logger.info('scheduler: job completed: autotask check and run')


def make_logs():
    logger.warning('This is a warning')


log_test = JobToAdd(func=make_logs, trigger=CronTrigger(second='*/10'), id='make_logs')


jobs_to_add = [
    JobToAdd(
        func=decrease_task_priority,
        trigger=daily_1am_trigger,
        id='daily_decrease_task_priority',
    ),
    JobToAdd(
        func=check_and_run_autotasks,
        trigger=daily_1am_trigger,
        id='check_for_autotasks_to_run',
    ),
]
