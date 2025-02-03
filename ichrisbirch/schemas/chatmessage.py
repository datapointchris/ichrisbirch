from pydantic import BaseModel
from pydantic import ConfigDict


class ChatMessageConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ChatMessageCreate(ChatMessageConfig):
    chat_id: int | None = None
    role: str
    content: str


class ChatMessage(ChatMessageConfig):
    id: int
    chat_id: int
    role: str
    content: str


class ChatMessageUpdate(ChatMessageConfig):
    chat_id: int | None = None
    role: str | None = None
    content: str
