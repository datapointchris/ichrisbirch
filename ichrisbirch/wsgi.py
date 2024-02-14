import logging

from ichrisbirch.api.main import create_api
from ichrisbirch.app.main import create_app
from ichrisbirch.config import get_settings
from ichrisbirch.scheduler.main import create_scheduler

logger = logging.getLogger(__name__)

settings = get_settings()
logger.info(f'loaded settings for environment: {settings.environment}')

app = create_app(settings=settings)
logger.info('created ichrisbirch app')

api = create_api(settings=settings)
logger.info('created ichrisbirch api')

scheduler = create_scheduler(settings=settings)
logger.info('created scheduler')
