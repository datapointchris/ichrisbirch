import structlog
from openai import OpenAI
from streamlit_cookies_controller import CookieController

from ichrisbirch.chat.api import ChatAPIClient
from ichrisbirch.chat.app import ChatApp
from ichrisbirch.chat.auth import ChatAuthClient
from ichrisbirch.config import Settings

logger = structlog.get_logger()


def create_chat_app(settings: Settings) -> ChatApp:
    logger.info('chat_app_creating')
    app = ChatApp(
        settings=settings,
        chat_api_client=ChatAPIClient(),
        auth_client=ChatAuthClient(settings=settings),
        cookie_controller=CookieController(),
        ai_client=OpenAI(api_key=settings.ai.openai.api_key),
    )
    logger.info('chat_app_created')
    return app
