import logging

import streamlit as st
from openai import OpenAI
from streamlit import session_state as ss
from streamlit_cookies_controller import CookieController

from ichrisbirch import models
from ichrisbirch.chat.api import ChatAPI
from ichrisbirch.chat.auth import ChatAuthClient
from ichrisbirch.config import settings
from ichrisbirch.util import find_project_root

logger = logging.getLogger('chat.app')
st.set_page_config(page_title='Chatter', page_icon='🤖', layout='wide')

USER_AVATAR = '👤'
BOT_AVATAR = '🤖'
STYLESHEET = find_project_root() / 'ichrisbirch' / 'chat' / 'styles.css'

auth = ChatAuthClient(settings=settings)
cookie = CookieController()
openai = OpenAI(api_key=settings.ai.openai.api_key)


def generate_chat_session_name(prompt, client):
    response = client.chat.completions.create(
        model=settings.ai.openai.model,
        messages=[
            {
                'role': 'system',
                'content': 'Give a short, descriptive name to this chat prompt.',
            },
            {'role': 'user', 'content': prompt},
        ],
        max_tokens=10,
    )
    if name := response.choices[0].message.content:
        logger.info(f'generated name for chat session: {name}')
        return name.strip()
    else:
        logger.warning('failed to generate a summary for the chat session')
        return generate_chat_session_name(prompt, client)


def initialize_session():
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


def user_must_be_logged_in():
    initialize_session()

    if ss.logged_in:
        return True

    if access_token := cookie.get('access_token'):
        logger.info('found access token in cookie')
    if refresh_token := cookie.get('refresh_token'):
        logger.info('found refresh token in cookie')

    if access_token and auth.validate_jwt_token(access_token):
        logger.info(f'access token is: {access_token[-10:]}')
        logger.info('validated access token')
        ss.access_token = access_token
        if user := auth.login_token(access_token):
            ss.user = user
            ss.logged_in = True
            return True
        logger.info('failed to log in user with access token')

    if refresh_token:
        if new_access_token := auth.refresh_access_token(refresh_token):
            logger.info('refreshed access token')
            cookie.set('access_token', new_access_token)
            ss.access_token = new_access_token
            if user := auth.login_token(new_access_token):
                ss.user = user
                ss.logged_in = True
                return True
            else:
                logger.info('failed to log in user with refreshed access token')
        else:
            logger.info('failed to refresh access token')
        ss.access_token = None
        ss.refresh_token = None
        cookie.remove('access_token')
        cookie.remove('refresh_token')

    display_login_form()
    return ss.logged_in


def display_login_form():
    with st.form('LoginForm', clear_on_submit=True):
        st.text_input('Username', key='username', value=ss.get('username', ''))
        st.text_input('Password', type='password', key='password', value='')
        st.form_submit_button('Log in', on_click=login_flow)


def login_flow():
    if user := auth.login_username(ss.get('username', ''), ss.get('password', '')):
        if tokens := auth.request_jwt_tokens(user, ss['password']):
            logger.info(f'jwt tokens received for user: {user.email}')
            ss.access_token = tokens.get("access_token")
            ss.refresh_token = tokens.get("refresh_token")
            cookie.set('access_token', ss.access_token)
            cookie.set('refresh_token', ss.refresh_token)
            ss.logged_in = True
            ss.user = user
            logger.debug(f'session user: {ss.user.email}')
        else:
            logger.error('failed to obtain jwt tokens')
            st.error('Failed to obtain JWT tokens')
    else:
        st.error('Login Error')
        logger.warning(f'error trying to log in user: {ss["username"]}')
    ss.pop("password", None)


def logout_user():
    logger.debug(f'logging out user: {ss.user.email}')
    try:
        auth.logout_user(ss.user, ss.access_token)
    except Exception as e:
        logger.error(f'error logging out user: {e}')
    cookie.remove('access_token')
    cookie.remove('refresh_token')
    ss.logged_in = False
    ss.user = None
    ss.access_token = None
    ss.refresh_token = None
    ss.current_chat_index = None
    logger.info('user logged out')


if not user_must_be_logged_in():
    st.stop()

chat_api = ChatAPI(user=ss.user)

if 'chats' not in ss:
    ss.chats = chat_api.get_all_chats()
    ss.current_chat_index = None


with STYLESHEET.open() as f:
    logger.debug(f'Loading custom stylesheet: {STYLESHEET.resolve()}')
    styles = f.read()

st.markdown(f'<style>{styles}</style>', unsafe_allow_html=True)

with st.sidebar:
    if st.button('Logout'):
        logout_user()
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
        chat_name = chat.name or f'Chat {i+1}'
        if st.button(chat_name):
            ss.current_chat_index = i


if ss.current_chat_index is None and ss.chats:
    ss.current_chat_index = 0

if ss.current_chat_index is not None:
    current_chat = ss.chats[ss.current_chat_index]
    for message in current_chat.messages:
        avatar = USER_AVATAR if message.role == 'user' else BOT_AVATAR
        with st.chat_message(message.role, avatar=avatar):
            st.markdown(message.content)

    prompt = st.chat_input('How can I help?')
    if prompt:
        current_chat.messages.append(models.ChatMessage(chat_id=current_chat.id, role='user', content=prompt))

        # set session name automatically after first question
        if not current_chat.name:
            current_chat.name = generate_chat_session_name(prompt, openai)

        with st.chat_message('user', avatar=USER_AVATAR):
            st.markdown(prompt)

        with st.chat_message('assistant', avatar=BOT_AVATAR):
            message_placeholder = st.empty()
            full_response = ''
            current_messages = [{'role': m.role, 'content': m.content} for m in current_chat.messages]
            stream = openai.chat.completions.create(
                model=settings.ai.openai.model,
                messages=current_messages,  # type: ignore
                stream=True,
            )  # type: ignore
            for chunk in stream:
                full_response += chunk.choices[0].delta.content or ''  # type: ignore
                message_placeholder.markdown(full_response + '|')
            message_placeholder.markdown(full_response)
        current_chat.messages.append(
            models.ChatMessage(chat_id=current_chat.id, role='assistant', content=full_response)
        )

    if not ss.anon_chat:
        # Don't save anonymous chat sessions
        if current_chat.name:
            # Save chat sessions after each interaction
            # but only after the first prompt and response to generate a name from
            if existing_chat := chat_api.get_chat(current_chat.name):
                logger.info(f'found chat session: {current_chat.name}')
                updated_chat = chat_api.update_chat(existing_chat, current_chat)
            else:
                logger.info(f'chat session not found: {current_chat.name}, creating...')
                if updated_chat := chat_api.create_new_chat(current_chat):
                    logger.info(f'created new chat session: {chat.name}')
                    ss.chats[ss.current_chat_index] = updated_chat
