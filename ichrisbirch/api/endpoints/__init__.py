import logging

logger = logging.getLogger(__name__)
logger.debug('before importing api endpoints')
from ichrisbirch.api.endpoints import autotasks, countdowns, events, health, home, tasks  # noqa: F401, E402

logger.debug('after importing api endpoints')
