from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from ichrisbirch.database.sqlalchemy.base import Base

if TYPE_CHECKING:
    from ichrisbirch.models.chat import Chat


class ChatMessage(Base):
    __table_args__ = {'schema': 'chat'}
    __tablename__ = 'messages'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey('chat.chats.id', ondelete='CASCADE'), nullable=False)
    chat: Mapped['Chat'] = relationship(back_populates='messages')
    role: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.now)

    def __repr__(self) -> str:
        return f"""ChatMessage(
        id={self.id!r},
        chat_id={self.chat_id!r},
        role={self.role!r},
        content={self.content!r},
        )"""
