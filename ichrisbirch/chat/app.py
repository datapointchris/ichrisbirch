import json
import logging
from pathlib import Path

import streamlit as st
from openai import OpenAI

from ichrisbirch.config import get_settings

settings = get_settings()
logger = logging.getLogger('app.chat')
st.set_page_config(page_title='Chatter', page_icon='🤖')

USER_AVATAR = '👤'
BOT_AVATAR = '🤖'
DB_NAME = Path('chat_history.json')
CUSTOM_STYLESHEET = 'chat/styles.css'
client = OpenAI(api_key=settings.ai.openai.api_key)


def load_chat_sessions():
    if DB_NAME.exists():
        with DB_NAME.open() as file:
            logger.info(f'Loading chat history from: {DB_NAME}')
            return json.load(file)
    logger.warning(f'Could not find chat history file at: {DB_NAME}')
    return []


def save_chat_sessions(chat_sessions):
    with DB_NAME.open('w') as file:
        json.dump(chat_sessions, file)


def create_name_for_session(prompt):
    summary_response = client.chat.completions.create(
        model=st.session_state['openai_model'],
        messages=[
            {
                'role': 'system',
                'content': 'Summarize the following prompt in a few words.',
            },
            {'role': 'user', 'content': prompt},
        ],
        max_tokens=10,
    )
    if summary := summary_response.choices[0].message.content:
        return summary.strip()
    else:
        logger.warning('Failed to generate a summary for the chat session')
        return create_name_for_session(prompt)


if 'openai_model' not in st.session_state:
    st.session_state['openai_model'] = settings.ai.openai.model


if 'chat_sessions' not in st.session_state:
    st.session_state.chat_sessions = load_chat_sessions()
    st.session_state.current_session = None


with open(CUSTOM_STYLESHEET) as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

with st.sidebar:
    st.write("<h1 class='sidebar-title'>Chat Sessions</h1>", unsafe_allow_html=True)
    for i, session in enumerate(st.session_state.chat_sessions):
        session_name = session.get('name', f'Session {i+1}')
        if st.button(session_name):
            st.session_state.current_session = i

    if st.button('New Chat Session'):
        new_session = {'name': '', 'messages': []}
        st.session_state.chat_sessions.append(new_session)
        st.session_state.current_session = len(st.session_state.chat_sessions) - 1


if st.session_state.current_session is None and st.session_state.chat_sessions:
    st.session_state.current_session = len(st.session_state.chat_sessions) - 1


if st.session_state.current_session is not None:
    current_session = st.session_state.chat_sessions[st.session_state.current_session]
    for message in current_session['messages']:
        avatar = USER_AVATAR if message['role'] == 'user' else BOT_AVATAR
        with st.chat_message(message['role'], avatar=avatar):
            st.markdown(message['content'])

    if prompt := st.chat_input('How can I help?'):
        current_session['messages'].append({'role': 'user', 'content': prompt})

        # set session name automatically after first question
        if not current_session['name']:
            current_session['name'] = create_name_for_session(prompt)

        with st.chat_message('user', avatar=USER_AVATAR):
            st.markdown(prompt)

        with st.chat_message('assistant', avatar=BOT_AVATAR):
            message_placeholder = st.empty()
            full_response = ''
            for response in client.chat.completions.create(
                model=st.session_state['openai_model'],
                messages=current_session['messages'],
                stream=True,
            ):
                full_response += response.choices[0].delta.content or ''
                message_placeholder.markdown(full_response + '|')
            message_placeholder.markdown(full_response)
        current_session['messages'].append({'role': 'assistant', 'content': full_response})

    # Save chat sessions after each interaction
    save_chat_sessions(st.session_state.chat_sessions)
