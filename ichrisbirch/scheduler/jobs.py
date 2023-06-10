from ichrisbirch import models
from sqlalchemy import select, and_
import logging
from ichrisbirch.database.sqlalchemy.session import sqlalchemy_session
from datetime import datetime


logger = logging.getLogger(__name__)


def decrease_task_priority(session=sqlalchemy_session):
    """Decrease priority of all tasks by 1 each day"""
    session = next(session())
    query = select(models.Task).filter(and_(models.Task.priority > 1, models.Task.complete_date.is_(None)))
    for task in session.scalars(query).all():
        task.priority -= 1
    session.commit()
    session.close()
    logger.info('Daily task priority decrease complete')


def check_and_run_autotasks(session=sqlalchemy_session):
    """Check if any autotasks should run today and create tasks if so"""
    session = next(session())
    for autotask in session.scalars(select(models.AutoTask)).all():
        if autotask.should_run_today:
            task = models.Task(
                name=autotask.name, category=autotask.category, priority=autotask.priority, notes=autotask.notes
            )
            session.add(task)
            autotask.last_run_date = datetime.now().isoformat()
            autotask.run_count += 1
    logger.info('Daily autotask check complete')
    session.commit()
