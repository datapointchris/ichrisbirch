import logging

import httpx
import streamlit as st
from openai import OpenAI

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.app import utils
from ichrisbirch.config import get_settings
from ichrisbirch.util import find_project_root

settings = get_settings()
logger = logging.getLogger('app.chat')
st.set_page_config(page_title='Chatter', page_icon='🤖', layout='wide')

USER_AVATAR = '👤'
BOT_AVATAR = '🤖'
STYLESHEET = find_project_root() / 'ichrisbirch' / 'chat' / 'styles.css'
openai_client = OpenAI(api_key=settings.ai.openai.api_key)


class ChatAPI:
    def __init__(self, api_url: str):
        self.api_url = api_url
        self.client = httpx.Client(follow_redirects=True)
        self.chat_url = f'{settings.api_url}/chat/chats/'
        self.message_url = f'{settings.api_url}/chat/messages/'

    def _convert_chat_to_model(self, chat: dict):
        if chat['messages']:
            chat['messages'] = [models.ChatMessage(**message) for message in chat['messages']]
        return models.Chat(**chat)

    def get_chat(self, name: str):
        response = self.client.get(utils.url_builder(self.chat_url, name)).raise_for_status()
        if chat := response.json():
            return self._convert_chat_to_model(chat)

    def get_all_chats(self):
        response = self.client.get(self.chat_url).raise_for_status()
        if chats := response.json():
            return [self._convert_chat_to_model(chat) for chat in chats]
        return []

    def create_new_chat(self, chat: models.Chat):
        json_model = schemas.ChatCreate.model_validate(chat).model_dump()
        response = self.client.post(self.chat_url, json=json_model).raise_for_status()
        if new_chat := response.json():
            logger.info(f'created new chat session: {chat.name}')
        return self._convert_chat_to_model(new_chat)

    def update_chat(self, existing_chat: models.Chat, chat: models.Chat):
        if new_messages := [m for m in chat.messages if m.id not in [m.id for m in existing_chat.messages]]:
            for message in new_messages:
                msg_info = {
                    'id': {message.id},
                    'chat_id': {message.chat_id},
                    'role': {message.role},
                    'content': {message.content[:20]},
                }
                logger.info(f'found new message: {msg_info}')
                # NOTE: ChatMessageCreate DOES NOT WORK, it erases the chat_id
                json_model = dict(chat_id=message.chat_id or chat.id, role=message.role, content=message.content)
                response = self.client.post(self.message_url, json=json_model)
                response.raise_for_status()
                logger.info(f'created new message: {str(response.json())[:100]}')
            return self.get_chat(chat.name)
        return chat

    def save_chat_session(self, chat: models.Chat):
        if existing_chat := self.get_chat(chat.name):
            logger.info(f'found chat session: {chat.name}')
            return self.update_chat(existing_chat, chat)
        else:
            logger.info(f'chat session not found: {chat.name}, creating...')
            return self.create_new_chat(chat)


def create_name_for_session(prompt):
    response = openai_client.chat.completions.create(
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
        print('okay')
        return create_name_for_session(prompt)


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
            current_chat.name = create_name_for_session(prompt)

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
