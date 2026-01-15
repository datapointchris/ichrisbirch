import re
from collections.abc import Iterable
from pathlib import Path

import structlog
from fastapi import APIRouter
from fastapi import Cookie
from fastapi import Depends
from fastapi import HTTPException
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from fastapi import status
from pygtail import Pygtail
from sqlalchemy import select
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.endpoints.auth import get_admin_user
from ichrisbirch.api.endpoints.auth import validate_jwt_token
from ichrisbirch.api.endpoints.auth import validate_user_id
from ichrisbirch.config import Settings
from ichrisbirch.config import get_settings
from ichrisbirch.database.backup import DatabaseBackup
from ichrisbirch.database.session import get_sqlalchemy_session
from ichrisbirch.logger import LOG_DIR

logger = structlog.get_logger()
router = APIRouter()
# Separate router for WebSocket (no global auth dependency - handles its own auth)
ws_router = APIRouter()

# Regex to strip ANSI escape codes from log lines
ANSI_ESCAPE_PATTERN = re.compile(r'\x1b\[[0-9;]*m')


class LogReader:
    """Log reader that reads from all log files in the log directory."""

    def __init__(self, log_dir: str = LOG_DIR):
        self.log_dir = Path(log_dir)

    def get_logs(self) -> Iterable[str]:
        """Read new logs from all *.log files in the log directory."""
        if not self.log_dir.exists():
            logger.warning('log_dir_not_found', log_dir=str(self.log_dir))
            return

        log_files = sorted(self.log_dir.glob('*.log'))
        logger.debug('log_reader_init', log_dir=str(self.log_dir), files=[f.name for f in log_files])

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
    access_token: str | None = Cookie(default=None),
    settings: Settings = Depends(get_settings),
    session=Depends(get_sqlalchemy_session),
):
    """WebSocket endpoint for streaming logs. Authenticates via cookie."""
    # Authenticate via cookie
    if not access_token:
        logger.warning('websocket_no_token')
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        # Cookie value is "Bearer <token>", strip the prefix
        token = access_token.removeprefix('Bearer ')
        user_id = validate_jwt_token(token, settings)
        if not user_id:
            logger.warning('websocket_invalid_token')
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Look up user and check admin status
        user = validate_user_id(user_id, session)
        if not user or not user.is_admin:
            logger.warning('websocket_not_admin', user_id=user_id)
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        logger.debug('websocket_admin_authenticated', email=user.email)
    except Exception as e:
        logger.warning('websocket_auth_failed', error=str(e))
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    logger.debug('websocket_connect', url=str(websocket.url))
    await websocket.accept()
    logger.debug('websocket_accepted')

    try:
        for line in log_reader.get_logs():
            await websocket.send_text(line)
    except WebSocketDisconnect:
        logger.debug('websocket_client_disconnected')
    except Exception as e:
        logger.error('websocket_stream_error', error=str(e))
    finally:
        logger.debug('websocket_closed')
        await websocket.close()


@router.post('/backups/', response_model=schemas.BackupResult, status_code=status.HTTP_201_CREATED)
async def create_backup(
    backup_request: schemas.BackupCreate,
    user: models.User = Depends(get_admin_user),
):
    """Create a new database backup."""
    logger.info('backup_create_request', description=backup_request.description, user_id=user.id)

    if not backup_request.upload_to_s3 and not backup_request.save_local:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='At least one of upload_to_s3 or save_local must be True',
        )

    db_backup = DatabaseBackup()
    record = db_backup.backup(
        description=backup_request.description,
        upload=backup_request.upload_to_s3,
        save_local=backup_request.save_local,
        backup_type='manual',
        user_id=user.id,
    )

    logger.info('backup_created', success=record.success, filename=record.filename, backup_id=record.id)

    if not record.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Backup failed: {record.error_message}',
        )

    return record


@router.get('/backups/', response_model=list[schemas.Backup], status_code=status.HTTP_200_OK)
async def read_backups(
    session: Session = Depends(get_sqlalchemy_session),
    limit: int = 50,
):
    """Get backup history."""
    query = select(models.BackupHistory).order_by(models.BackupHistory.created_at.desc()).limit(limit)
    return list(session.scalars(query).all())


@router.get('/backups/{id}/', response_model=schemas.Backup, status_code=status.HTTP_200_OK)
async def read_backup(id: int, session: Session = Depends(get_sqlalchemy_session)):
    """Get a single backup record."""
    if backup := session.get(models.BackupHistory, id):
        return backup
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Backup {id} not found')
