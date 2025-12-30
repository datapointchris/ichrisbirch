"""Chat and ChatMessage factories for generating test objects."""

from datetime import datetime

import factory

from ichrisbirch.models.chat import Chat
from ichrisbirch.models.chatmessage import ChatMessage

from .base import get_factory_session


class ChatFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating Chat objects."""

    class Meta:
        model = Chat
        sqlalchemy_session_factory = get_factory_session
        sqlalchemy_session_persistence = 'flush'

    name = factory.Sequence(lambda n: f'Test Chat {n + 1}')
    category = 'General'
    subcategory = None
    tags = factory.LazyFunction(lambda: ['test'])
    created_at = factory.LazyFunction(datetime.now)

    class Params:
        # Usage: ChatFactory(with_subcategory=True)
        with_subcategory = factory.Trait(subcategory='Subcategory')


class ChatMessageFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating ChatMessage objects.

    By default creates an associated Chat.
    """

    class Meta:
        model = ChatMessage
        sqlalchemy_session_factory = get_factory_session
        sqlalchemy_session_persistence = 'flush'

    role = 'user'
    content = factory.Sequence(lambda n: f'Test message {n + 1}')
    created_at = factory.LazyFunction(datetime.now)

    # SubFactory creates a chat automatically
    chat = factory.SubFactory(ChatFactory)
    chat_id = factory.LazyAttribute(lambda obj: obj.chat.id if obj.chat else None)

    class Params:
        # Usage: ChatMessageFactory(assistant=True)
        assistant = factory.Trait(role='assistant')
        # Usage: ChatMessageFactory(system=True)
        system = factory.Trait(role='system')

    @classmethod
    def in_chat(cls, chat: Chat, **kwargs):
        """Create a message in a specific chat."""
        return cls(chat=chat, **kwargs)

    @classmethod
    def user_message(cls, content: str, **kwargs):
        """Create a user message with specific content."""
        return cls(role='user', content=content, **kwargs)

    @classmethod
    def assistant_message(cls, content: str, **kwargs):
        """Create an assistant message with specific content."""
        return cls(role='assistant', content=content, **kwargs)
