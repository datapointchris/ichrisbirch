from ichrisbirch.api.main import create_api
from ichrisbirch.config import get_settings

settings = get_settings()
api = create_api(settings=settings)
