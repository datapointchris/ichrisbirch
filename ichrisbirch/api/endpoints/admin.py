import hashlib
import hmac
import re
import shutil
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pendulum
import structlog
from fastapi import APIRouter
from fastapi import Cookie
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from fastapi import status
from pygtail import Pygtail
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api import smoke_tests
from ichrisbirch.api.endpoints.auth import DbSession
from ichrisbirch.api.endpoints.auth import get_admin_user
from ichrisbirch.api.endpoints.auth import validate_user_id
from ichrisbirch.api.middleware import recent_errors
from ichrisbirch.api.redis_client import get_redis_client
from ichrisbirch.config import Settings
from ichrisbirch.config import get_settings
from ichrisbirch.database.session import get_sqlalchemy_session
from ichrisbirch.logger import LOG_DIR
from ichrisbirch.scheduler.main import get_jobstore

logger = structlog.get_logger()
router = APIRouter()
# Separate router for WebSocket (no global auth dependency - handles its own auth)
ws_router = APIRouter()

# Regex to strip ANSI escape codes from log lines
ANSI_ESCAPE_PATTERN = re.compile(r'\x1b\[[0-9;]*m')

# WebSocket auth token validity (24 hours)
WS_AUTH_TOKEN_VALIDITY_SECONDS = 86400


def validate_ws_auth_token(token: str | None, settings: Settings, session: Session) -> models.User | None:
    """Validate WebSocket auth token signed by Flask frontend.

    Token format: user_id:timestamp:signature
    Signature is HMAC-SHA256 of "user_id:timestamp" using internal_service_key.
    """
    if not token:
        return None
    try:
        parts = token.split(':')
        if len(parts) != 3:
            logger.debug('ws_auth_token_invalid_format')
            return None

        user_id, timestamp_str, signature = parts
        timestamp = int(timestamp_str)

        # Check token age
        age = int(time.time()) - timestamp
        if age > WS_AUTH_TOKEN_VALIDITY_SECONDS or age < 0:
            logger.debug('ws_auth_token_expired', age=age)
            return None

        # Verify signature
        message = f'{user_id}:{timestamp_str}'
        expected = hmac.new(settings.auth.internal_service_key.encode(), message.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            logger.warning('ws_auth_token_invalid_signature')
            return None

        # Look up user and verify admin status
        user = validate_user_id(user_id, session)
        if not user:
            logger.warning('ws_auth_user_not_found', user_id=user_id)
            return None
        if not user.is_admin:
            logger.warning('ws_auth_user_not_admin', user_id=user_id)
            return None

        return user
    except Exception as e:
        logger.warning('ws_auth_token_validation_error', error=str(e))
        return None


class LogReader:
    """Log reader that reads from all log files in the log directory."""

    def __init__(self, log_dir: str = LOG_DIR):
        self.log_dir = Path(log_dir)
        log_files = sorted(self.log_dir.glob('*.log')) if self.log_dir.exists() else []
        logger.debug('log_reader_init', log_dir=str(self.log_dir), files=[f.name for f in log_files])

    def get_logs(self) -> Iterable[str]:
        """Read new logs from all *.log files in the log directory."""
        if not self.log_dir.exists():
            logger.warning('log_dir_not_found', log_dir=str(self.log_dir))
            return

        log_files = sorted(self.log_dir.glob('*.log'))

        for log_file in log_files:
            try:
                for line in Pygtail(str(log_file), paranoid=True):
                    # Strip ANSI escape codes before yielding
                    yield ANSI_ESCAPE_PATTERN.sub('', line)
            except Exception as e:
                logger.error('log_reader_error', file=log_file.name, error=str(e))


# Default log reader dependency
def get_log_reader() -> LogReader:
    """Default log reader implementation."""
    return LogReader()


@ws_router.websocket('/log-stream/')
async def websocket_endpoint_log(
    websocket: WebSocket,
    log_reader: LogReader = Depends(get_log_reader),
    ws_auth: str | None = Cookie(default=None),
    settings: Settings = Depends(get_settings),
    session=Depends(get_sqlalchemy_session),
):
    """WebSocket endpoint for streaming logs. Authenticates via signed token from Flask."""
    # Authenticate via signed token cookie (set by Flask frontend)
    user = validate_ws_auth_token(ws_auth, settings, session)
    if not user:
        logger.warning('websocket_auth_failed', has_token=bool(ws_auth))
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    logger.debug('websocket_admin_authenticated', email=user.email)

    logger.debug('websocket_connect', url=str(websocket.url))
    await websocket.accept()
    logger.debug('websocket_accepted')

    try:
        import asyncio

        # Continuously stream logs until client disconnects
        while True:
            has_logs = False
            for line in log_reader.get_logs():
                await websocket.send_text(line)
                has_logs = True

            # If no new logs, wait before checking again
            if not has_logs:
                await asyncio.sleep(1)
    except WebSocketDisconnect:
        logger.debug('websocket_client_disconnected')
    except Exception as e:
        logger.error('websocket_stream_error', error=str(e))
    finally:
        logger.debug('websocket_closed')


# --- Scheduler endpoints ---


def _format_time_until(next_run_time) -> str:
    """Format the time until next run as a human-readable string."""
    if next_run_time is None:
        return 'Paused'
    return pendulum.interval(pendulum.now(next_run_time.tzinfo), next_run_time).in_words()


@router.get('/scheduler/jobs/', response_model=list[schemas.SchedulerJob])
async def list_scheduler_jobs(settings: Settings = Depends(get_settings)):
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
async def pause_scheduler_job(job_id: str, settings: Settings = Depends(get_settings)):
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
async def resume_scheduler_job(job_id: str, settings: Settings = Depends(get_settings)):
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
async def delete_scheduler_job(job_id: str, settings: Settings = Depends(get_settings)):
    """Delete a scheduler job from the jobstore."""
    jobstore = get_jobstore(settings=settings)
    job = jobstore.lookup_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Job {job_id} not found')
    jobstore.remove_job(job_id)
    logger.info('scheduler_job_deleted', job_id=job_id)


@router.get('/scheduler/history/', response_model=list[schemas.SchedulerJobRun])
async def get_scheduler_history(
    session: DbSession,
    job_id: str | None = None,
    limit: int = 50,
):
    """Get scheduler job run history, optionally filtered by job_id."""
    query = select(models.SchedulerJobRun).order_by(models.SchedulerJobRun.started_at.desc())
    if job_id:
        query = query.where(models.SchedulerJobRun.job_id == job_id)
    query = query.limit(limit)
    return list(session.scalars(query).all())


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


# --- System health endpoints ---

SENSITIVE_FIELD_KEYWORDS = {'key', 'secret', 'password', 'token'}


def _get_docker_containers() -> list[schemas.admin.DockerContainerStatus]:
    """Get status of Docker containers, gracefully handling unavailability."""
    try:
        import docker

        client = docker.from_env()
        containers = client.containers.list(all=True, filters={'name': 'icb-'})
        return [
            schemas.admin.DockerContainerStatus(
                name=c.name,
                status=c.status,
                started_at=c.attrs.get('State', {}).get('StartedAt'),
                image=','.join(c.image.tags) if c.image.tags else c.image.short_id,
            )
            for c in sorted(containers, key=lambda c: c.name)
        ]
    except Exception as e:
        logger.warning('docker_status_unavailable', error=str(e))
        return []


def _get_database_stats(session: Session) -> schemas.admin.DatabaseStats:
    """Get database statistics via raw SQL."""
    rows = session.execute(text('SELECT schemaname, relname, n_live_tup FROM pg_stat_user_tables ORDER BY schemaname, relname')).fetchall()
    tables = [schemas.admin.TableRowCount(schema_name=r[0], table_name=r[1], row_count=r[2]) for r in rows]

    size_result = session.execute(text('SELECT pg_database_size(current_database())')).scalar()
    total_size_mb = round((size_result or 0) / (1024 * 1024), 2)

    conn_result = session.execute(text('SELECT count(*) FROM pg_stat_activity')).scalar()

    return schemas.admin.DatabaseStats(tables=tables, total_size_mb=total_size_mb, active_connections=conn_result or 0)


def _get_redis_stats(settings: Settings) -> schemas.admin.RedisStats:
    """Get Redis server statistics."""
    try:
        client = get_redis_client(settings)
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
        return schemas.admin.RedisStats(key_count=0, memory_used_human='N/A', connected_clients=0, uptime_seconds=0)


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
async def get_system_health(
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
async def get_recent_errors():
    """Get recent 4xx/5xx errors from the in-memory ring buffer."""
    return list(recent_errors)


@router.get('/config/', response_model=list[schemas.admin.EnvironmentConfigSection])
async def get_environment_config(settings: Settings = Depends(get_settings)):
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
