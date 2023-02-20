from ichrisbirch import base_logger
from ichrisbirch.api.main import create_api
from ichrisbirch.app.main import create_app
from ichrisbirch.config import settings

base_logger.init(settings)

app = create_app(settings)
api = create_api(settings)
