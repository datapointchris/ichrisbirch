import logging

logger = logging.getLogger(__name__)
logger.debug('before importing api endpoints')
from ichrisbirch.api.endpoints import autotasks, box_packing, countdowns, events, health, home, tasks  # noqa: F401, E402

__all__ = ['autotasks', 'box_packing', 'countdowns', 'events', 'health', 'home', 'tasks']

logger.debug('after importing api endpoints')
