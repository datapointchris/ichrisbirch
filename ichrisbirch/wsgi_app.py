import logging

from ichrisbirch.app.main import create_app
from ichrisbirch.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()
logger.info(f'loaded settings for environment: {settings.environment}')

app = create_app(settings=settings)
logger.info('created ichrisbirch app')
