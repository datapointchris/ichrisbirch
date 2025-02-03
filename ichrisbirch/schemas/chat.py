from pydantic import BaseModel
from pydantic import ConfigDict

from ichrisbirch.schemas.chatmessage import ChatMessage
from ichrisbirch.schemas.chatmessage import ChatMessageCreate


class ChatConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ChatCreate(ChatConfig):
    name: str
    category: str | None = None
    subcategory: str | None = None
    tags: list[str] | None = None
    messages: list['ChatMessageCreate']


class Chat(ChatConfig):
    id: int
    name: str
    category: str | None = None
    subcategory: str | None = None
    tags: list[str] | None = None
    messages: list['ChatMessage']


class ChatUpdate(ChatConfig):
    name: str | None = None
    category: str | None = None
    subcategory: str | None = None
    tags: list[str] | None = None
    messages: list['ChatMessage']
