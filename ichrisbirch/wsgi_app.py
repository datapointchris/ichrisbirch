from ichrisbirch.app.main import create_app
from ichrisbirch.config import get_settings

app = create_app(settings=get_settings())
