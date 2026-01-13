import structlog

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.client.logging_client import logging_internal_service_client

logger = structlog.get_logger()


class ChatAPIClient:
    def __init__(self, user: models.User | None = None):
        # Use internal service auth since Streamlit doesn't have Flask sessions
        self._client = logging_internal_service_client()
        self.chat_api = self._client.resource('chat/chats', schemas.Chat)
        self.chat_messages_api = self._client.resource('chat/messages', schemas.ChatMessage)

    def close(self):
        """Close the API client connection."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _convert_chat_to_model(self, chat: schemas.Chat):
        """The chat messages are not automatically converted to models, so must be done manually.

        Known issue with SQLAchemy, other workarounds are more verbose and involve metaprogramming.
        """
        if chat.messages:
            messages = [models.ChatMessage(**message.model_dump()) for message in chat.messages]
        return models.Chat(**(chat.model_dump() | {'messages': messages}))

    def get_chat(self, name: str):
        if chat := self.chat_api.get_one(name):
            return self._convert_chat_to_model(chat)
        return None

    def get_all_chats(self):
        if chats := self.chat_api.get_many():
            return [self._convert_chat_to_model(chat) for chat in chats]
        return []

    def create_new_chat(self, chat: models.Chat):
        json_model = schemas.ChatCreate.model_validate(chat).model_dump()
        if new_chat := self.chat_api.post(json=json_model):
            return self._convert_chat_to_model(new_chat)
        return None

    def update_chat(self, existing_chat: models.Chat, current_chat: models.Chat):
        existing_chat_message_ids = [m.id for m in existing_chat.messages]
        new_chat_messages = [m for m in current_chat.messages if m.id not in existing_chat_message_ids]
        for message in new_chat_messages:
            msg_info = {
                'id': message.id,
                'chat_id': message.chat_id,
                'role': message.role,
                'content': message.content[:20],
            }
            logger.info('found_new_chat_message', msg_info=msg_info)
            # NOTE: ChatMessageCreate DOES NOT WORK, it erases the chat_id
            json_model = dict(chat_id=message.chat_id or current_chat.id, role=message.role, content=message.content)
            if new_message := self.chat_messages_api.post(json=json_model):
                logger.info('chat_message_created', content_preview=new_message.content[:20])
        return self.get_chat(current_chat.name)
