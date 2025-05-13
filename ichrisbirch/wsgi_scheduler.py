from ichrisbirch.config import get_settings
from ichrisbirch.scheduler.main import create_scheduler

scheduler = create_scheduler(settings=get_settings())
