import logging
from typing import Iterable

from fastapi import APIRouter
from fastapi import Depends
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from pygtail import Pygtail

from ichrisbirch.util import get_logger_filename_from_handlername

logger = logging.getLogger('api.admin')
router = APIRouter()


class LogReader:
    """Log reader class that abstracts the log reading implementation."""

    def get_logs(self) -> Iterable[str]:
        """Read logs from the application log file."""
        try:
            log_filename = get_logger_filename_from_handlername('ichrisbirch_file')
            logger.debug(f'Reading logs from: {log_filename}')
            return Pygtail(log_filename, paranoid=True)
        except Exception as e:
            logger.error(f"Error setting up log reader: {e}")
            return []


# Default log reader dependency
def get_log_reader() -> LogReader:
    """Default log reader implementation."""
    return LogReader()


@router.websocket('/log-stream/')
async def websocket_endpoint_log(websocket: WebSocket, log_reader: LogReader = Depends(get_log_reader)):
    logger.debug(f'websocket url: {websocket.url}')
    logger.debug(f'websocket headers: {websocket.headers}')
    await websocket.accept()
    logger.debug('websocket accepted')

    try:
        for line in log_reader.get_logs():
            await websocket.send_text(line)
    except WebSocketDisconnect:
        logger.debug('Client disconnected')
    except Exception as e:
        logger.error(f"Error in websocket stream: {e}")
    finally:
        logger.debug('closed websocket')
        await websocket.close()
