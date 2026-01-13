from collections.abc import Iterable

import structlog
from fastapi import APIRouter
from fastapi import Depends
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from pygtail import Pygtail

from ichrisbirch.util import get_logger_filename_from_handlername

logger = structlog.get_logger()
router = APIRouter()


class LogReader:
    """Log reader class that abstracts the log reading implementation."""

    def get_logs(self) -> Iterable[str]:
        """Read logs from the application log file."""
        try:
            log_filename = get_logger_filename_from_handlername('ichrisbirch_file')
            logger.debug('log_reader_init', filename=log_filename)
            return Pygtail(log_filename, paranoid=True)
        except Exception as e:
            logger.error('log_reader_error', error=str(e))
            return []


# Default log reader dependency
def get_log_reader() -> LogReader:
    """Default log reader implementation."""
    return LogReader()


@router.websocket('/log-stream/')
async def websocket_endpoint_log(websocket: WebSocket, log_reader: LogReader = Depends(get_log_reader)):
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
