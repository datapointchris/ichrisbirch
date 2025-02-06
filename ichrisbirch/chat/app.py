import logging

import streamlit as st
from openai import OpenAI

from ichrisbirch import models
from ichrisbirch.chat.api import ChatAPI
from ichrisbirch.chat.auth import ChatAuthClient
from ichrisbirch.config import get_settings
from ichrisbirch.util import find_project_root

settings = get_settings()
logger = logging.getLogger('app.chat')
st.set_page_config(page_title='Chatter', page_icon='🤖', layout='wide')

USER_AVATAR = '👤'
BOT_AVATAR = '🤖'
STYLESHEET = find_project_root() / 'ichrisbirch' / 'chat' / 'styles.css'

chat_auth_client = ChatAuthClient(settings=settings)
openai_client = OpenAI(api_key=settings.ai.openai.api_key)
chat_api = ChatAPI(settings=settings)


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


def user_logged_in():
    logger.info('initializing session')
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "access_token" not in st.session_state:
        st.session_state.access_token = None
    if "refresh_token" not in st.session_state:
        st.session_state.refresh_token = None

    if st.session_state.logged_in:
        return True

    if not (st.session_state.access_token and chat_auth_client.validate_jwt_token(st.session_state.access_token)):
        logger.info('no access token found, or token is invalid, trying to refresh')
        if st.session_state.refresh_token:
            if access_token := chat_auth_client.refresh_access_token(st.session_state.refresh_token):
                st.session_state.access_token = access_token
                st.session_state.logged_in = True
                return True
            logger.info('failed to refresh access token, displaying login form')
            display_login_form()
            if not st.session_state.logged_in:
                return False
    return True


def display_login_form():
    with st.form("LoginForm"):
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        st.form_submit_button("Log in", on_click=login_flow)


def login_flow():
    if user := chat_auth_client.login_user(st.session_state['username'], st.session_state['password']):
        if tokens := chat_auth_client.request_jwt_tokens(user, st.session_state['password']):
            st.session_state.access_token = tokens.get("access_token")
            st.session_state.refresh_token = tokens.get("refresh_token")
            logger.info(f'JWT tokens received for user: {user.name}')
            st.session_state.logged_in = True
        else:
            logger.error('failed to obtain jwt tokens')
            st.error('Failed to obtain JWT tokens')
    else:
        st.error('Invalid username or password')
        logger.warning(f'invalid login attempt for: {st.session_state["username"]}')
    st.session_state.pop("username", None)
    st.session_state.pop("password", None)


if not user_logged_in():
    st.stop()


if 'chats' not in st.session_state:
    st.session_state.chats = chat_api.get_all_chats()
    st.session_state.current_session = None


with STYLESHEET.open() as f:
    logger.info(f'Loading custom stylesheet: {STYLESHEET.resolve()}')
    styles = f.read()

st.markdown(f'<style>{styles}</style>', unsafe_allow_html=True)

with st.sidebar:
    if st.button('Logout'):
        chat_auth_client.logout_user(st.session_state.access_token)
        st.session_state.logged_in = False
        st.session_state.access_token = None
        st.session_state.refresh_token = None
        logger.info('user logged out')
        st.rerun()

    st.write("<h1 class='sidebar-title'>Chats</h1>", unsafe_allow_html=True)
    for i, chat in enumerate(st.session_state.chats):
        chat_name = chat.name or f'Chat {i+1}'
        if st.button(chat_name):
            st.session_state.current_session = i

    if st.button('New Chat'):
        new_chat = models.Chat(name='', messages=[])
        st.session_state.chats.append(new_chat)
        st.session_state.current_session = len(st.session_state.chats) - 1

if st.session_state.current_session is None and st.session_state.chats:
    st.session_state.current_session = len(st.session_state.chats) - 1

if st.session_state.current_session is not None:
    current_chat = st.session_state.chats[st.session_state.current_session]
    for message in current_chat.messages:
        avatar = USER_AVATAR if message.role == 'user' else BOT_AVATAR
        with st.chat_message(message.role, avatar=avatar):
            st.markdown(message.content)

    prompt = st.chat_input('How can I help?')
    if prompt:
        current_chat.messages.append(models.ChatMessage(chat_id=current_chat.id, role='user', content=prompt))

        # set session name automatically after first question
        if not current_chat.name:
            current_chat.name = generate_chat_session_name(prompt, openai_client)

        with st.chat_message('user', avatar=USER_AVATAR):
            st.markdown(prompt)

        with st.chat_message('assistant', avatar=BOT_AVATAR):
            message_placeholder = st.empty()
            full_response = ''
            current_messages = [{'role': m.role, 'content': m.content} for m in current_chat.messages]
            stream = openai_client.chat.completions.create(
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

    # Save chat sessions after each interaction
    # but only after the first prompt and response to generate a name from
    if current_chat.name:
        if existing_chat := chat_api.get_chat(chat.name):
            logger.info(f'found chat session: {chat.name}')
            updated_chat = chat_api.update_chat(existing_chat, chat)
        else:
            logger.info(f'chat session not found: {chat.name}, creating...')
            updated_chat = chat_api.create_new_chat(chat)
        st.session_state.chats[st.session_state.current_session] = updated_chat
