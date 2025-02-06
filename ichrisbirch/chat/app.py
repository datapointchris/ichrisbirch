import logging

import streamlit as st
from openai import OpenAI

from ichrisbirch import models
from ichrisbirch.chat.api import ChatAPI
from ichrisbirch.chat.auth import logout_user
from ichrisbirch.chat.auth import require_user_logged_in
from ichrisbirch.config import get_settings
from ichrisbirch.util import find_project_root

settings = get_settings()
logger = logging.getLogger('app.chat')
st.set_page_config(page_title='Chatter', page_icon='🤖', layout='wide')

USER_AVATAR = '👤'
BOT_AVATAR = '🤖'
STYLESHEET = find_project_root() / 'ichrisbirch' / 'chat' / 'styles.css'


def create_name_for_session(prompt, client):
    response = client.chat.completions.create(
        model=st.session_state['openai_model'],
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
        logger.info(f'Generated name for chat session: {name}')
        return name.strip()
    else:
        logger.warning('Failed to generate a summary for the chat session')
        return create_name_for_session(prompt, client)


if not require_user_logged_in():
    st.stop()


openai_client = OpenAI(api_key=settings.ai.openai.api_key)
chat_api = ChatAPI(settings.api_url)

if 'openai_model' not in st.session_state:
    st.session_state['openai_model'] = settings.ai.openai.model


if 'chats' not in st.session_state:
    st.session_state.chats = chat_api.get_all_chats()
    st.session_state.current_session = None


with STYLESHEET.open() as f:
    logger.info(f'Loading custom stylesheet: {STYLESHEET.resolve()}')
    styles = f.read()

st.markdown(f'<style>{styles}</style>', unsafe_allow_html=True)

with st.sidebar:
    if st.button('Logout'):
        logout_user()
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
            current_chat.name = create_name_for_session(prompt, openai_client)

        with st.chat_message('user', avatar=USER_AVATAR):
            st.markdown(prompt)

        with st.chat_message('assistant', avatar=BOT_AVATAR):
            message_placeholder = st.empty()
            full_response = ''
            current_messages = [{'role': m.role, 'content': m.content} for m in current_chat.messages]
            stream = openai_client.chat.completions.create(
                model=st.session_state['openai_model'],
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
        if updated_chat := chat_api.save_chat_session(current_chat):
            st.session_state.chats[st.session_state.current_session] = updated_chat
        else:
            logger.error('Failed to save chat session')
