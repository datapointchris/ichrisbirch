from ichrisbirch.api.main import create_api
from ichrisbirch.app.main import create_app
from ichrisbirch.config import get_settings
from ichrisbirch.logger import create_base_logger
from ichrisbirch.scheduler.main import create_scheduler

settings = get_settings()
logger = create_base_logger()
app = create_app()
api = create_api()
scheduler = create_scheduler()
