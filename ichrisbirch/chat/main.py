import logging

import streamlit as st
from openai import OpenAI
from streamlit import session_state as ss
from streamlit_cookies_controller import CookieController

from ichrisbirch.chat.api import ChatAPI
from ichrisbirch.chat.app import ChatApp
from ichrisbirch.chat.auth import ChatAuthClient
from ichrisbirch.config import Settings

logger = logging.getLogger(__name__)
st.set_page_config(page_title='Chatter', page_icon='🤖', layout='wide')


def create_chat_app(settings: Settings) -> ChatApp:
    logger.info('creating chat app')
    app = ChatApp(
        settings=settings,
        api_client=ChatAPI(user=ss.user),
        auth_client=ChatAuthClient(settings=settings),
        cookie_controller=CookieController(),
        ai_client=OpenAI(api_key=settings.ai.openai.api_key),
    )
    logger.info('chat app created')
    return app
