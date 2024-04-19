import logging

from ichrisbirch.api.main import create_api
from ichrisbirch.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()
logger.info(f'loaded settings for environment: {settings.ENVIRONMENT}')

api = create_api(settings=settings)
logger.info('created ichrisbirch api')
