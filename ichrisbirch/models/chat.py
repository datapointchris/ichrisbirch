from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from ichrisbirch.database.sqlalchemy.base import Base

if TYPE_CHECKING:
    from ichrisbirch.models.chatmessage import ChatMessage


class Chat(Base):
    __table_args__ = {'schema': 'chat'}
    __tablename__ = 'chats'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    category: Mapped[str] = mapped_column(Text, nullable=True)
    subcategory: Mapped[str] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str]] = mapped_column(postgresql.ARRAY(Text), nullable=True)
    messages: Mapped[list['ChatMessage']] = relationship(back_populates='chat', order_by='ChatMessage.created_at')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.now)

    def __repr__(self) -> str:
        return f"""Chat(
        id={self.id!r},
        name={self.name!r},
        category={self.category!r},
        subcategory={self.subcategory!r},
        tags={self.tags!r},
        messages={self.messages!r},
        )"""
