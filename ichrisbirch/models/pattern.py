from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Identity
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from ichrisbirch.database.base import Base


class Pattern(Base):
    __tablename__ = 'patterns'
    id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    def __repr__(self):
        return f'Pattern(message={self.message}, recorded_at={self.recorded_at})'
