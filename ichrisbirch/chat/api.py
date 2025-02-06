import logging

import httpx

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.app import utils
from ichrisbirch.config import get_settings

settings = get_settings()
logger = logging.getLogger('app.chat_api')


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
