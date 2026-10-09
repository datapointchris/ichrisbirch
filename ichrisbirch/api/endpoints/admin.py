import shutil
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from typing import Any

import docker
import pendulum
import structlog
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api import smoke_tests
from ichrisbirch.api.endpoints.auth import DbSession
from ichrisbirch.api.endpoints.auth import get_admin_user
from ichrisbirch.api.middleware import recent_errors
from ichrisbirch.api.redis_client import get_redis_client
from ichrisbirch.config import Settings
from ichrisbirch.config import get_settings
from ichrisbirch.scheduler.main import get_jobstore
from ichrisbirch.services.row_limit import CappedRowLimit
from ichrisbirch.services.row_limit import apply_row_limit

logger = structlog.get_logger()
router = APIRouter()


# --- Scheduler endpoints ---


def _format_time_until(next_run_time) -> str:
    """Format the time until next run as a human-readable string."""
    if next_run_time is None:
        return 'Paused'
    return pendulum.interval(pendulum.now(next_run_time.tzinfo), next_run_time).in_words()


@router.get('/scheduler/jobs/', response_model=list[schemas.SchedulerJob])
def list_scheduler_jobs(settings: Settings = Depends(get_settings)):
    """List all APScheduler jobs with their status."""
    jobstore = get_jobstore(settings=settings)
    jobs = jobstore.get_all_jobs()
    return [
        schemas.SchedulerJob(
            id=job.id,
            name=job.name,
            trigger=str(job.trigger),
            next_run_time=job.next_run_time,
            time_until_next_run=_format_time_until(job.next_run_time),
            is_paused=job.next_run_time is None,
        )
        for job in jobs
    ]


@router.post('/scheduler/jobs/{job_id}/pause/', response_model=schemas.SchedulerJob)
def pause_scheduler_job(job_id: str, settings: Settings = Depends(get_settings)):
    """Pause a scheduler job by setting next_run_time to None."""
    jobstore = get_jobstore(settings=settings)
    job = jobstore.lookup_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Job {job_id} not found')
    job.next_run_time = None
    jobstore.update_job(job)
    logger.info('scheduler_job_paused', job_id=job_id)
    return schemas.SchedulerJob(
        id=job.id,
        name=job.name,
        trigger=str(job.trigger),
        next_run_time=None,
        time_until_next_run='Paused',
        is_paused=True,
    )


@router.post('/scheduler/jobs/{job_id}/resume/', response_model=schemas.SchedulerJob)
def resume_scheduler_job(job_id: str, settings: Settings = Depends(get_settings)):
    """Resume a paused scheduler job by recalculating next_run_time."""
    jobstore = get_jobstore(settings=settings)
    job = jobstore.lookup_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Job {job_id} not found')
    job.next_run_time = job.trigger.get_next_fire_time(None, pendulum.now())
    jobstore.update_job(job)
    logger.info('scheduler_job_resumed', job_id=job_id, next_run_time=str(job.next_run_time))
    return schemas.SchedulerJob(
        id=job.id,
        name=job.name,
        trigger=str(job.trigger),
        next_run_time=job.next_run_time,
        time_until_next_run=_format_time_until(job.next_run_time),
        is_paused=False,
    )


@router.delete('/scheduler/jobs/{job_id}/', status_code=status.HTTP_204_NO_CONTENT)
def delete_scheduler_job(job_id: str, settings: Settings = Depends(get_settings)):
    """Delete a scheduler job from the jobstore."""
    jobstore = get_jobstore(settings=settings)
    job = jobstore.lookup_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Job {job_id} not found')
    jobstore.remove_job(job_id)
    logger.info('scheduler_job_deleted', job_id=job_id)


@router.get('/scheduler/history/', response_model=list[schemas.SchedulerJobRun])
def get_scheduler_history(
    session: DbSession,
    job_id: str | None = None,
    limit: CappedRowLimit = 50,
):
    """Get scheduler job run history, optionally filtered by job_id."""
    query = select(models.SchedulerJobRun).order_by(models.SchedulerJobRun.started_at.desc())
    if job_id:
        query = query.where(models.SchedulerJobRun.job_id == job_id)
    return list(session.scalars(apply_row_limit(query, limit)).all())


# --- Smoke tests ---


@router.post('/smoke-tests/', response_model=schemas.admin.SmokeTestReport)
async def run_smoke_tests_endpoint(
    request: Request,
    user: models.User = Depends(get_admin_user),
    settings: Settings = Depends(get_settings),
):
    """Run smoke tests against all GET endpoints."""
    logger.info('smoke_tests_requested', user_id=user.id)
    return await smoke_tests.run_smoke_tests(request.app, settings, user.email)


# --- Signup settings ---


@router.get('/signup-settings/', response_model=schemas.SignupSettings)
def get_signup_settings(session: DbSession):
    """Whether `POST /users/` creates an account."""
    return session.scalars(select(models.SignupSettings)).one()


@router.patch('/signup-settings/', response_model=schemas.SignupSettings)
def update_signup_settings(
    update: schemas.SignupSettingsUpdate,
    session: DbSession,
    user: models.User = Depends(get_admin_user),
):
    """Open or close signups. The next `POST /users/` reads the new state."""
    signup_settings = session.scalars(select(models.SignupSettings)).one()
    for attr, value in update.model_dump(exclude_unset=True).items():
        setattr(signup_settings, attr, value)
    session.commit()
    session.refresh(signup_settings)
    logger.info('signup_settings_updated', user_id=user.id, is_open=signup_settings.is_open)
    return signup_settings


# --- System health endpoints ---

SENSITIVE_FIELD_KEYWORDS = {'key', 'secret', 'password', 'token'}

# Each probe call, and the Docker probe as a whole, gets this long before it reads as unavailable.
PROBE_TIMEOUT_SECONDS = 2

TABLE_ROW_COUNTS_SQL = text('SELECT schemaname, relname, n_live_tup FROM pg_stat_user_tables ORDER BY schemaname, relname')
DATABASE_SIZE_SQL = text('SELECT pg_database_size(current_database())')
CONNECTION_COUNT_SQL = text('SELECT count(*) FROM pg_stat_activity')

# A slow daemon holds one thread at most, however often the page refreshes. A health read arriving
# meanwhile queues behind that thread until its own deadline.
_docker_probe_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='docker-probe')


def _list_docker_containers() -> list[schemas.admin.DockerContainerStatus]:
    with closing(docker.from_env(timeout=PROBE_TIMEOUT_SECONDS)) as client:
        statuses = []
        for container in sorted(client.containers.list(all=True, filters={'name': 'icb-'}), key=lambda c: c.name):
            image = container.image
            statuses.append(
                schemas.admin.DockerContainerStatus(
                    name=container.name,
                    status=container.status,
                    started_at=container.attrs.get('State', {}).get('StartedAt'),
                    image=','.join(image.tags) if image.tags else image.short_id,
                )
            )
        return statuses


def _get_docker_containers() -> list[schemas.admin.DockerContainerStatus] | None:
    """None when the daemon errors or misses the deadline. An empty list means it answered and no container matched."""
    probe = _docker_probe_executor.submit(_list_docker_containers)
    try:
        return probe.result(timeout=PROBE_TIMEOUT_SECONDS)
    except TimeoutError:
        probe.cancel()
        logger.warning('docker_status_unavailable', error=f'no answer within {PROBE_TIMEOUT_SECONDS}s')
        return None
    except Exception as e:
        logger.warning('docker_status_unavailable', error=str(e))
        return None


def _get_database_stats(session: Session) -> schemas.admin.DatabaseStats | None:
    """Get database statistics via raw SQL."""
    try:
        session.execute(
            text("SELECT set_config('statement_timeout', :timeout_ms, true)"),
            {'timeout_ms': str(round(PROBE_TIMEOUT_SECONDS * 1000))},
        )
        rows = session.execute(TABLE_ROW_COUNTS_SQL).fetchall()
        size_result = session.execute(DATABASE_SIZE_SQL).scalar()
        conn_result = session.execute(CONNECTION_COUNT_SQL).scalar()
    except OperationalError as e:
        session.rollback()
        logger.warning('database_stats_unavailable', error=str(e))
        return None

    tables = [schemas.admin.TableRowCount(schema_name=r[0], table_name=r[1], row_count=r[2]) for r in rows]
    total_size_mb = round((size_result or 0) / (1024 * 1024), 2)
    return schemas.admin.DatabaseStats(tables=tables, total_size_mb=total_size_mb, active_connections=conn_result or 0)


def _get_redis_stats(settings: Settings) -> schemas.admin.RedisStats | None:
    """Get Redis server statistics."""
    try:
        with get_redis_client(settings, read_timeout=PROBE_TIMEOUT_SECONDS) as client:
            info = client.info()
        db_info = info.get(f'db{settings.redis.db}', {})
        key_count = db_info.get('keys', 0) if isinstance(db_info, dict) else 0
        return schemas.admin.RedisStats(
            key_count=key_count,
            memory_used_human=info.get('used_memory_human', 'N/A'),
            connected_clients=info.get('connected_clients', 0),
            uptime_seconds=info.get('uptime_in_seconds', 0),
        )
    except Exception as e:
        logger.warning('redis_stats_unavailable', error=str(e))
        return None


def _get_disk_usage() -> schemas.admin.DiskUsage:
    """Get disk usage for the root filesystem."""
    usage = shutil.disk_usage('/')
    return schemas.admin.DiskUsage(
        total_gb=round(usage.total / (1024**3), 2),
        used_gb=round(usage.used / (1024**3), 2),
        free_gb=round(usage.free / (1024**3), 2),
        percent_used=round(usage.used / usage.total * 100, 1),
    )


def _mask_settings_value(key: str, value: object) -> Any:
    """Mask sensitive settings values based on field name."""
    key_lower = key.lower()
    if any(keyword in key_lower for keyword in SENSITIVE_FIELD_KEYWORDS):
        return '***MASKED***'
    return value


def _serialize_settings_section(section: object) -> dict:
    """Serialize a settings section to a dict with secrets masked."""
    result = {}
    for attr in sorted(dir(section)):
        if attr.startswith('_'):
            continue
        value = getattr(section, attr)
        if callable(value):
            continue
        if hasattr(value, '__dict__') and value is not None and not isinstance(value, str | list | dict | int | float | bool):
            result[attr] = _serialize_settings_section(value)
        else:
            result[attr] = _mask_settings_value(attr, value)
    return result


@router.get('/system/health/', response_model=schemas.admin.SystemHealth)
def get_system_health(
    session: DbSession,
    settings: Settings = Depends(get_settings),
):
    """Get combined system health information."""
    bluegreen_state = Path('/var/lib/ichrisbirch/bluegreen-state')
    deploy_color = bluegreen_state.read_text().strip() if bluegreen_state.exists() else None
    return schemas.admin.SystemHealth(
        server=schemas.admin.ServerInfo(
            environment=settings.ENVIRONMENT,
            api_url=settings.api_url,
            server_time=pendulum.now().isoformat(timespec='seconds'),
            deploy_color=deploy_color,
        ),
        docker=_get_docker_containers(),
        database=_get_database_stats(session),
        redis=_get_redis_stats(settings),
        disk=_get_disk_usage(),
    )


@router.get('/system/errors/', response_model=list[schemas.admin.RecentError])
def get_recent_errors():
    """Get recent 4xx/5xx errors from the in-memory ring buffer."""
    return list(recent_errors)


@router.get('/config/', response_model=list[schemas.admin.EnvironmentConfigSection])
def get_environment_config(settings: Settings = Depends(get_settings)):
    """Get environment configuration with sensitive values masked."""
    sections = []
    for attr in sorted(dir(settings)):
        if attr.startswith('_'):
            continue
        value = getattr(settings, attr)
        if callable(value):
            continue
        if hasattr(value, '__dict__') and value is not None and not isinstance(value, str | list | dict | int | float | bool):
            sections.append(
                schemas.admin.EnvironmentConfigSection(
                    name=attr,
                    settings=_serialize_settings_section(value),
                )
            )
        else:
            if not sections or sections[0].name != '_general':
                sections.insert(0, schemas.admin.EnvironmentConfigSection(name='_general', settings={}))
            sections[0].settings[attr] = _mask_settings_value(attr, value)
    return sections
