import logging

from ichrisbirch.config import get_settings
from ichrisbirch.scheduler.main import create_scheduler

logger = logging.getLogger('scheduler')

settings = get_settings()
logger.info(f'loaded settings for environment: {settings.ENVIRONMENT}')

scheduler = create_scheduler(settings=settings)
