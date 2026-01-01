import logging
import re

import streamlit as st
from openai import OpenAI
from streamlit import session_state as ss
from streamlit_cookies_controller import CookieController

from ichrisbirch import models
from ichrisbirch.chat.api import ChatAPIClient
from ichrisbirch.chat.auth import ChatAuthClient
from ichrisbirch.config import Settings
from ichrisbirch.config import get_settings
from ichrisbirch.util import find_project_root

logger = logging.getLogger(__name__)
st.set_page_config(page_title='Chatter', page_icon='🤖', layout='wide')


class ChatApp:
    def __init__(
        self,
        settings: Settings,
        chat_api_client: ChatAPIClient,
        auth_client: ChatAuthClient,
        cookie_controller: CookieController,
        ai_client: OpenAI,
    ):
        self.settings = settings
        self.api = chat_api_client
        self.auth = auth_client
        self.cookies = cookie_controller
        self.ai = ai_client

    USER_AVATAR = '👤'
    BOT_AVATAR = '🤖'
    STYLESHEET = find_project_root() / 'ichrisbirch' / 'chat' / 'styles.css'

    def _initialize_session(self):
        logger.info('initializing chat app session')

        if 'logged_in' not in ss:
            ss.logged_in = False
        else:
            logger.debug(f'logged_in: {ss.logged_in}')

        if 'user' not in ss:
            ss.user = None
        else:
            logger.debug(f'user: {ss.user}')

        if 'access_token' not in ss or ss.access_token is None:
            ss.access_token = None
        else:
            logger.debug(f'access_token: {ss.access_token[-10:]}')

        if 'refresh_token' not in ss or ss.refresh_token is None:
            ss.refresh_token = None
        else:
            logger.debug(f'refresh_token: {ss.refresh_token[-10:]}')

        if 'current_chat_index' not in ss:
            ss.current_chat_index = None
        else:
            logger.debug(f'current_chat_index: {ss.current_chat_index}')

        if 'anon_chat' not in ss:
            ss.anon_chat = False
        else:
            logger.debug(f'anon_chat: {ss.anon_chat}')

    def display_login_form(self):
        with st.form('LoginForm', clear_on_submit=True):
            st.text_input('Username', key='username', value=ss.get('username', ''))
            st.text_input('Password', type='password', key='password', value='')
            st.form_submit_button('Log in', on_click=self.login_flow)

    def login_flow(self):
        if user := self.auth.login_username(ss.get('username', ''), ss.get('password', '')):
            if tokens := self.auth.request_jwt_tokens(user, ss['password']):
                logger.info(f'jwt tokens received for user: {user.email}')
                ss.access_token = tokens.get('access_token')
                ss.refresh_token = tokens.get('refresh_token')
                self.cookies.set('access_token', ss.access_token)
                self.cookies.set('refresh_token', ss.refresh_token)
                ss.logged_in = True
                ss.user = user
                logger.debug(f'session user: {ss.user.email}')
            else:
                logger.error('failed to obtain jwt tokens')
                st.error('Failed to obtain JWT tokens')
        else:
            st.error('Login Error')
            logger.warning(f'error trying to log in user: {ss["username"]}')
        ss.pop('password', None)

    def user_must_be_logged_in(self):
        self._initialize_session()

        if ss.logged_in:
            return True

        if access_token := self.cookies.get('access_token'):
            logger.info('found access token in cookie')
        if refresh_token := self.cookies.get('refresh_token'):
            logger.info('found refresh token in cookie')

        if access_token and self.auth.validate_jwt_token(access_token):
            logger.info(f'access token is: {access_token[-10:]}')
            logger.info('validated access token')
            ss.access_token = access_token
            if user := self.auth.login_token(access_token):
                ss.user = user
                ss.logged_in = True
                return True
            logger.info('failed to log in user with access token')

        if refresh_token:
            if new_access_token := self.auth.refresh_access_token(refresh_token):
                logger.info('refreshed access token')
                self.cookies.set('access_token', new_access_token)
                ss.access_token = new_access_token
                if user := self.auth.login_token(new_access_token):
                    ss.user = user
                    ss.logged_in = True
                    return True
                else:
                    logger.info('failed to log in user with refreshed access token')
            else:
                logger.info('failed to refresh access token')
            ss.access_token = None
            ss.refresh_token = None
            self.cookies.remove('access_token')
            self.cookies.remove('refresh_token')

        self.display_login_form()
        return ss.logged_in

    def logout_user(self):
        logger.debug(f'logging out user: {ss.user.email}')
        try:
            self.auth.logout_user(ss.user, ss.access_token)
        except Exception as e:
            logger.error(f'error logging out user: {e}')
        self.cookies.remove('access_token')
        self.cookies.remove('refresh_token')
        ss.logged_in = False
        ss.user = None
        ss.access_token = None
        ss.refresh_token = None
        ss.current_chat_index = None
        logger.info('user logged out')

    def generate_chat_session_name(self, prompt):
        attempts = 0
        while attempts < 3:
            response = self.ai.chat.completions.create(
                model=self.settings.ai.openai.model,
                messages=[
                    {
                        'role': 'system',
                        'content': """Give a short, descriptive name to this chat prompt that will be used as the prompt title.

                                   Do not use special characters or line breaks.
                                   """,
                    },
                    {'role': 'user', 'content': prompt},
                ],
                max_completion_tokens=10,
            )
            if name := response.choices[0].message.content:
                logger.info(f'generated name for chat session: {name}')
                # Remove any characters not allowed in a URL path segment
                safe_name = re.sub(r'[^A-Za-z0-9\-_.~]', '', name.strip())
                return safe_name
            else:
                logger.warning('failed to generate a summary for the chat session')
            attempts += 1
        return f'Chat Session - {prompt[:20]}...'

    def create_sidebar(self):
        with st.sidebar:
            if st.button('Logout'):
                self.logout_user()
                st.rerun()

            if st.button('Anon Chat'):
                ss.anon_chat = True
                new_chat = models.Chat(name='', messages=[])
                ss.chats.append(new_chat)
                ss.current_chat_index = len(ss.chats) - 1

            if st.button('New Chat'):
                new_chat = models.Chat(name='', messages=[])
                ss.chats.append(new_chat)
                ss.current_chat_index = len(ss.chats) - 1

            st.write("<h1 class='sidebar-title'>Chats</h1>", unsafe_allow_html=True)
            for i, chat in enumerate(ss.chats):
                chat_name = chat.name or f'Chat {i + 1}'
                if st.button(chat_name):
                    ss.current_chat_index = i

    def display_chat(self):
        if ss.current_chat_index is None and ss.chats:
            ss.current_chat_index = 0

        if ss.current_chat_index is not None:
            current_chat = ss.chats[ss.current_chat_index]
            for message in current_chat.messages:
                avatar = self.USER_AVATAR if message.role == 'user' else self.BOT_AVATAR
                with st.chat_message(message.role, avatar=avatar):
                    st.markdown(message.content)

            prompt = st.chat_input('How can I help?')
            if prompt:
                current_chat.messages.append(models.ChatMessage(chat_id=current_chat.id, role='user', content=prompt))

                # set session name automatically after first question
                if not current_chat.name:
                    current_chat.name = self.generate_chat_session_name(prompt)

                with st.chat_message('user', avatar=self.USER_AVATAR):
                    st.markdown(prompt)

                with st.chat_message('assistant', avatar=self.BOT_AVATAR):
                    message_placeholder = st.empty()
                    full_response = ''
                    current_messages = [{'role': m.role, 'content': m.content} for m in current_chat.messages]
                    stream = self.ai.chat.completions.create(
                        model=self.settings.ai.openai.model,
                        messages=current_messages,  # type: ignore
                        stream=True,
                    )  # type: ignore
                    for chunk in stream:
                        full_response += chunk.choices[0].delta.content or ''  # type: ignore
                        message_placeholder.markdown(full_response + '|')
                    message_placeholder.markdown(full_response)
                current_chat.messages.append(models.ChatMessage(chat_id=current_chat.id, role='assistant', content=full_response))

            if not ss.anon_chat and current_chat.name:  # Don't save anonymous chat sessions
                # Save chat sessions after each interaction
                # but only after the first prompt and response to generate a name from
                if existing_chat := self.api.get_chat(current_chat.name):
                    logger.info(f'found chat session: {current_chat.name}')
                    updated_chat = self.api.update_chat(existing_chat, current_chat)
                else:
                    logger.info(f'chat session not found: {current_chat.name}, creating...')
                    if updated_chat := self.api.create_new_chat(current_chat):
                        logger.info(f'created new chat session: {current_chat.name}')
                        ss.chats[ss.current_chat_index] = updated_chat

    def run(self):
        logger.info('running app')
        if not self.user_must_be_logged_in():
            st.stop()

        if 'chats' not in ss:
            ss.chats = self.api.get_all_chats()
            ss.current_chat_index = None

        with self.STYLESHEET.open() as f:
            logger.debug(f'Loading custom stylesheet: {self.STYLESHEET.resolve()}')
            styles = f.read()

        st.markdown(f'<style>{styles}</style>', unsafe_allow_html=True)

        self.create_sidebar()
        self.display_chat()


logger.info('creating chat app')
_settings = get_settings()
app = ChatApp(
    settings=_settings,
    chat_api_client=ChatAPIClient(),
    auth_client=ChatAuthClient(settings=_settings),
    cookie_controller=CookieController(),
    ai_client=OpenAI(api_key=_settings.ai.openai.api_key),
)
logger.info('chat app created')
app.run()
