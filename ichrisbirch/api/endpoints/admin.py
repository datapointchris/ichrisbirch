import asyncio
import logging
import queue

from fastapi import APIRouter
from fastapi import WebSocket
from pygtail import Pygtail

logger = logging.getLogger('api.admin')
router = APIRouter()

log_queue: queue.Queue = queue.Queue()


async def read_new_logs():
    handler = logging.getHandlerByName('ichrisbirch_file')
    filename = handler.baseFilename
    for line in Pygtail(filename, paranoid=True):
        log_queue.put(line)


@router.websocket('/log-stream/')
async def websocket_endpoint_log(websocket: WebSocket):
    logger.debug(f'websocket: {websocket}')
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
