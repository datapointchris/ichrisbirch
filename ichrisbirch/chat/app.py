import re
import uuid

import streamlit as st
import structlog
from openai import OpenAI
from streamlit import session_state as ss
from streamlit_cookies_controller import CookieController

from ichrisbirch import models
from ichrisbirch.chat.api import ChatAPIClient
from ichrisbirch.chat.auth import ChatAuthClient
from ichrisbirch.config import Settings
from ichrisbirch.config import get_settings
from ichrisbirch.util import find_project_root

logger = structlog.get_logger()
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
        logger.info('chat_session_initializing')

        if 'logged_in' not in ss:
            ss.logged_in = False
        else:
            logger.debug('session_state_logged_in', value=ss.logged_in)

        if 'user' not in ss:
            ss.user = None
        else:
            logger.debug('session_state_user', value=str(ss.user))

        if 'access_token' not in ss or ss.access_token is None:
            ss.access_token = None
        else:
            logger.debug('session_state_access_token', token_suffix=ss.access_token[-10:])

        if 'refresh_token' not in ss or ss.refresh_token is None:
            ss.refresh_token = None
        else:
            logger.debug('session_state_refresh_token', token_suffix=ss.refresh_token[-10:])

        if 'current_chat_index' not in ss:
            ss.current_chat_index = None
        else:
            logger.debug('session_state_chat_index', value=ss.current_chat_index)

        if 'anon_chat' not in ss:
            ss.anon_chat = False
        else:
            logger.debug('session_state_anon_chat', value=ss.anon_chat)

    def display_login_form(self):
        with st.form('LoginForm', clear_on_submit=True):
            st.text_input('Username', key='username', value=ss.get('username', ''))
            st.text_input('Password', type='password', key='password', value='')
            st.form_submit_button('Log in', on_click=self.login_flow)

    def login_flow(self):
        if user := self.auth.login_username(ss.get('username', ''), ss.get('password', '')):
            if tokens := self.auth.request_jwt_tokens(user, ss['password']):
                logger.info('jwt_tokens_received', email=user.email)
                ss.access_token = tokens.get('access_token')
                ss.refresh_token = tokens.get('refresh_token')
                self.cookies.set('access_token', ss.access_token)
                self.cookies.set('refresh_token', ss.refresh_token)
                ss.logged_in = True
                ss.user = user
                logger.debug('session_user_set', email=ss.user.email)
            else:
                logger.error('jwt_tokens_failed')
                st.error('Failed to obtain JWT tokens')
        else:
            st.error('Login Error')
            logger.warning('login_error', username=ss.get('username', ''))
        ss.pop('password', None)

    def user_must_be_logged_in(self):
        self._initialize_session()

        if ss.logged_in:
            return True

        if access_token := self.cookies.get('access_token'):
            logger.debug('access_token_found_in_cookie')
        if refresh_token := self.cookies.get('refresh_token'):
            logger.debug('refresh_token_found_in_cookie')

        if access_token and self.auth.validate_jwt_token(access_token):
            logger.debug('access_token_validated', token_suffix=access_token[-10:])
            ss.access_token = access_token
            if user := self.auth.login_token(access_token):
                ss.user = user
                ss.logged_in = True
                return True
            logger.warning('access_token_login_failed')

        if refresh_token:
            if new_access_token := self.auth.refresh_access_token(refresh_token):
                logger.debug('access_token_refreshed')
                self.cookies.set('access_token', new_access_token)
                ss.access_token = new_access_token
                if user := self.auth.login_token(new_access_token):
                    ss.user = user
                    ss.logged_in = True
                    return True
                else:
                    logger.warning('refreshed_token_login_failed')
            else:
                logger.warning('access_token_refresh_failed')
            ss.access_token = None
            ss.refresh_token = None
            self.cookies.remove('access_token')
            self.cookies.remove('refresh_token')

        self.display_login_form()
        return ss.logged_in

    def logout_user(self):
        logger.debug('user_logging_out', email=ss.user.email)
        try:
            self.auth.logout_user(ss.user, ss.access_token)
        except Exception as e:
            # Silent failure: logout API call is non-critical
            # Local session cleanup still proceeds
            # User gets logged out regardless of API success
            logger.error('logout_api_error', error=str(e))
        self.cookies.remove('access_token')
        self.cookies.remove('refresh_token')
        ss.logged_in = False
        ss.user = None
        ss.access_token = None
        ss.refresh_token = None
        ss.current_chat_index = None
        logger.info('user_logged_out')

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
                logger.info('chat_session_name_generated', name=name)
                # Remove any characters not allowed in a URL path segment
                safe_name = re.sub(r'[^A-Za-z0-9\-_.~]', '', name.strip())
                return safe_name
            else:
                logger.warning('chat_session_name_generation_failed')
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
                structlog.contextvars.clear_contextvars()
                structlog.contextvars.bind_contextvars(request_id=str(uuid.uuid4())[:8])

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

                structlog.contextvars.clear_contextvars()

            if not ss.anon_chat and current_chat.name:  # Don't save anonymous chat sessions
                # Save chat sessions after each interaction
                # but only after the first prompt and response to generate a name from
                if existing_chat := self.api.get_chat(current_chat.name):
                    logger.debug('chat_session_found', name=current_chat.name)
                    updated_chat = self.api.update_chat(existing_chat, current_chat)
                else:
                    logger.debug('chat_session_creating', name=current_chat.name)
                    if updated_chat := self.api.create_new_chat(current_chat):
                        logger.info('chat_session_created', name=current_chat.name)
                        ss.chats[ss.current_chat_index] = updated_chat

    def run(self):
        logger.info('chat_app_running')
        if not self.user_must_be_logged_in():
            st.stop()

        if 'chats' not in ss:
            ss.chats = self.api.get_all_chats()
            ss.current_chat_index = None

        with self.STYLESHEET.open() as f:
            logger.debug('stylesheet_loading', path=str(self.STYLESHEET.resolve()))
            styles = f.read()

        st.markdown(f'<style>{styles}</style>', unsafe_allow_html=True)

        self.create_sidebar()
        self.display_chat()


logger.info('chat_app_creating')
_settings = get_settings()
app = ChatApp(
    settings=_settings,
    chat_api_client=ChatAPIClient(),
    auth_client=ChatAuthClient(settings=_settings),
    cookie_controller=CookieController(),
    ai_client=OpenAI(api_key=_settings.ai.openai.api_key),
)
logger.info('chat_app_created')
app.run()
