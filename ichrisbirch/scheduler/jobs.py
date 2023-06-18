import logging
from datetime import datetime

from sqlalchemy import and_, select

from ichrisbirch import models
from ichrisbirch.database.sqlalchemy.session import sqlalchemy_session

logger = logging.getLogger(__name__)


def decrease_task_priority(session=sqlalchemy_session) -> None:
    """Decrease priority of all tasks by 1 each day"""
    with next(session()) as session:
        query = select(models.Task).filter(and_(models.Task.priority > 1, models.Task.complete_date.is_(None)))
        for task in session.scalars(query).all():
            task.priority -= 1
        session.commit()
        logger.info('Daily task priority decrease complete')


def check_and_run_autotasks(session=sqlalchemy_session) -> None:
    """Check if any autotasks should run today and create tasks if so"""
    with next(session()) as session:
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
                autotask.last_run_date = datetime.now().isoformat()
                autotask.run_count += 1
        session.commit()
        logger.info('Daily autotask check complete')
