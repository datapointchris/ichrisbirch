import logging

from ichrisbirch.config import get_settings
from ichrisbirch.scheduler.main import create_scheduler

logger = logging.getLogger(__name__)

settings = get_settings()
logger.info(f'loaded settings for environment: {settings.environment}')

scheduler = create_scheduler(settings=settings)
logger.info('created scheduler')
try:
    scheduler.start()
    logger.info('scheduler started')
except (KeyboardInterrupt, SystemExit):
    pass
finally:
    scheduler.shutdown()
    logger.info('scheduler shutdown')
