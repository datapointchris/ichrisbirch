"""Jobs that run on the scheduler.

Jobs have to have the session created in this file,
since the session is not serializable and cannot be passed in as a parameter.
`SessionLocal` must be used instead of `get_sqlalchemy_session` because the generator produced
by the yield in `get_sqlalchemy_session` cannot be used as a context manager.
"""

import functools
import random
import subprocess  # nosec B404
from collections import defaultdict
from collections.abc import Callable
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pendulum
import structlog
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from ichrisbirch import models
from ichrisbirch.config import Settings
from ichrisbirch.database.session import create_session
from ichrisbirch.services.task_priorities import compact_incomplete_task_priorities
from ichrisbirch.util import find_project_root

logger = structlog.get_logger()


daily_1am_trigger = CronTrigger(day='*', hour=1)
daily_115am_trigger = CronTrigger(day='*', hour=1, minute=15)
daily_3pm_trigger = CronTrigger(day='*', hour=15)
weekly_sunday_3am_trigger = CronTrigger(day_of_week='sun', hour=3, minute=0)


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


def _persist_job_run(
    settings: Settings,
    job_id: str,
    started_at: datetime,
    finished_at: datetime,
    duration_seconds: float,
    success: bool,
    error_type: str | None = None,
    error_message: str | None = None,
) -> None:
    """Write a SchedulerJobRun record to the database."""
    try:
        with create_session(settings) as session:
            session.add(
                models.SchedulerJobRun(
                    job_id=job_id,
                    started_at=started_at,
                    finished_at=finished_at,
                    duration_seconds=duration_seconds,
                    success=success,
                    error_type=error_type,
                    error_message=error_message,
                )
            )
            session.commit()
    except Exception as e:
        logger.error('job_run_persist_failed', job_id=job_id, error=str(e))


def job_logger(func: Callable) -> Callable:
    """Decorator to log job start, completion, and failures.

    Exceptions are logged but swallowed to prevent one failing job
    from crashing the entire scheduler. Also persists a SchedulerJobRun
    record for each execution.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info('job_started', job_name=func.__name__)
        started_at = pendulum.now()
        success = False
        error_type = None
        error_message = None
        try:
            func(*args, **kwargs)
            success = True
            elapsed = (pendulum.now() - started_at).in_words()
            logger.info('job_completed', job_name=func.__name__, elapsed=elapsed)
        except Exception as e:
            elapsed = (pendulum.now() - started_at).in_words()
            error_type = type(e).__name__
            error_message = str(e)
            logger.error('job_failed', job_name=func.__name__, elapsed=elapsed, error_type=error_type, error=error_message)
        finally:
            finished_at = pendulum.now()
            duration_seconds = (finished_at - started_at).total_seconds()
            # settings is always the first positional arg to every job function
            settings = args[0] if args else kwargs.get('settings')
            if settings:
                _persist_job_run(
                    settings=settings,
                    job_id=func.__name__,
                    started_at=started_at,
                    finished_at=finished_at,
                    duration_seconds=duration_seconds,
                    success=success,
                    error_type=error_type,
                    error_message=error_message,
                )

    return wrapper


@job_logger
def make_logs(settings: Settings) -> None:
    logger.debug('scheduler_test_log', time=str(pendulum.now()))
    logger.info('scheduler_test_log', cwd=str(Path.cwd()))
    logger.info('scheduler_test_log', project_root=str(find_project_root()))
    logger.debug('scheduler_test_log', environment=settings.ENVIRONMENT)
    logger.warning('scheduler_test_warning')
    logger.error('scheduler_test_error_pause_job_to_stop')


@job_logger
def compact_task_priorities(settings: Settings) -> None:
    """Dense-rank incomplete tasks to priorities 1..K, tiebreak by add_date."""
    with create_session(settings) as session:
        count = compact_incomplete_task_priorities(session)
        session.commit()
        logger.info('task_priorities_compacted', count=count)


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
            logger.info('autotask_concurrent_count', autotask_name=autotask.name, concurrent=concurrent)
            if concurrent >= autotask.max_concurrent:
                logger.info(
                    'autotask_skipped_max_concurrent',
                    autotask_name=autotask.name,
                    concurrent=concurrent,
                    max_concurrent=autotask.max_concurrent,
                )
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
def check_and_run_autofun(settings: Settings) -> None:
    """Sync autofun active tasks then fill open slots from the fun list.

    Each run:
    1. For each active junction record, check if the linked task was completed
       or deleted; update the fun item accordingly and free the slot.
    2. While open slots remain (active < max_concurrent), pick a random
       available fun item and create a task for it.
    """
    with create_session(settings) as session:
        # Load scheduler settings from the single admin user's preferences
        admin_user = session.scalars(select(models.User).where(models.User.is_admin.is_(True))).first()
        if not admin_user:
            logger.warning('autofun_no_admin_user')
            return

        if admin_user.get_preference('autofun.is_paused'):
            logger.info('autofun_paused')
            return

        max_concurrent: int = admin_user.get_preference('autofun.max_concurrent')
        task_priority: int = admin_user.get_preference('autofun.task_priority')

        # Step 1: clean up completed or deleted tasks
        active_records = list(session.scalars(select(models.AutoFunActiveTask)).all())
        for record in active_records:
            task = session.get(models.Task, record.task_id)
            if task is None:
                # Task was deleted — free the slot, item stays available
                session.delete(record)
                logger.info('autofun_task_deleted', fun_item_id=record.fun_item_id)
            elif task.complete_date is not None:
                # Task was completed — mark the fun item done permanently
                fun_item = session.get(models.AutoFun, record.fun_item_id)
                if fun_item:
                    fun_item.is_completed = True
                    fun_item.completed_date = datetime.now()
                session.delete(record)
                logger.info('autofun_item_completed', fun_item_id=record.fun_item_id)

        session.flush()

        # Step 2: fill open slots
        remaining_active = list(session.scalars(select(models.AutoFunActiveTask)).all())
        active_item_ids = {r.fun_item_id for r in remaining_active}
        active_count = len(remaining_active)
        available = [
            item
            for item in session.scalars(select(models.AutoFun).where(models.AutoFun.is_completed.is_(False))).all()
            if item.id not in active_item_ids
        ]

        while active_count < max_concurrent and available:
            chosen = random.choice(available)
            available.remove(chosen)
            task = models.Task(
                name=chosen.name,
                notes=chosen.notes,
                category='Personal',
                priority=task_priority,
            )
            session.add(task)
            session.flush()
            session.add(models.AutoFunActiveTask(fun_item_id=chosen.id, task_id=task.id))
            active_count += 1
            logger.info('autofun_task_created', fun_item_id=chosen.id, task_id=task.id)

        session.commit()


@job_logger
def docker_prune(settings: Settings) -> None:
    """Weekly cleanup of old Docker images.

    Prunes images older than 7 days (168 hours) to free disk space while
    preserving recent build cache for faster rebuilds.

    Note: Requires Docker socket to be mounted to the scheduler container.
    Add to docker-compose.yml scheduler service:
        volumes:
          - /var/run/docker.sock:/var/run/docker.sock:ro
    """
    result = subprocess.run(  # nosec B603, B607
        ['docker', 'image', 'prune', '-af', '--filter', 'until=168h'],
        capture_output=True,
        text=True,
    )
    logger.info(
        'docker_prune_completed',
        stdout=result.stdout.strip() if result.stdout else '',
        stderr=result.stderr.strip() if result.stderr else '',
        return_code=result.returncode,
    )
    if result.returncode != 0:
        logger.error(
            'docker_prune_failed',
            return_code=result.returncode,
            stderr=result.stderr.strip() if result.stderr else '',
        )


def get_jobs_to_add(settings: Settings) -> list[JobToAdd]:
    """Get the list of jobs to add to the scheduler."""
    return [
        JobToAdd(
            func=make_logs,
            args=(settings,),
            trigger=CronTrigger(second=15),
            id='make_logs',
        ),
        JobToAdd(
            func=check_and_run_autotasks,
            args=(settings,),
            trigger=daily_1am_trigger,
            id='check_and_run_autotasks_daily',
        ),
        JobToAdd(
            func=check_and_run_autofun,
            args=(settings,),
            trigger=daily_1am_trigger,
            id='check_and_run_autofun_daily',
        ),
        JobToAdd(
            func=compact_task_priorities,
            args=(settings,),
            trigger=daily_115am_trigger,
            id='compact_task_priorities_daily',
        ),
        JobToAdd(
            func=docker_prune,
            args=(settings,),
            trigger=weekly_sunday_3am_trigger,
            id='docker_prune_weekly',
        ),
    ]
