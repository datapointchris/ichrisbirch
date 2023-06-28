import logging

from ichrisbirch.api.main import create_api
from ichrisbirch.app.main import create_app
from ichrisbirch.config import get_settings
from ichrisbirch.scheduler.main import create_scheduler

logger = logging.getLogger(__name__)

settings = get_settings()
logger.info(f'Loaded Settings for {settings.environment} environment')

app = create_app(settings=settings)
logger.info(f'Created ichrisbirch App in {settings.environment} environment')

api = create_api(settings=settings)
logger.info(f'Created ichrisbirch API in {settings.environment} environment')

scheduler = create_scheduler(settings=settings)
logger.info(f'Created Scheduler in {settings.environment} environment')
