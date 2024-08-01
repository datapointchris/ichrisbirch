import asyncio
import logging
import queue

from fastapi import APIRouter
from fastapi import WebSocket
from pygtail import Pygtail

from ichrisbirch.util import get_logger_filename_from_handlername

logger = logging.getLogger('api.admin')
router = APIRouter()

log_queue: queue.Queue = queue.Queue()

log_filename = get_logger_filename_from_handlername('ichrisbirch_file')  # noqa: FURB120


async def read_new_logs():
    for line in Pygtail(log_filename, paranoid=True):
        log_queue.put(line)


@router.websocket('/log-stream/')
async def websocket_endpoint_log(websocket: WebSocket):
    logger.debug(f'logstream source: {log_filename}')
    logger.debug(f'websocket: {websocket}')
    logger.debug(f'websocket: {websocket.base_url}')
    await websocket.accept()
    logger.debug('websocket accepted')

    try:
        while True:
            if not log_queue.empty():
                log = log_queue.get()
                await websocket.send_text(log)
            else:
                await read_new_logs()
                await asyncio.sleep(1)
    finally:
        logger.debug('closed websocket')
        await websocket.close()
