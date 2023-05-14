from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from ichrisbirch.db.sqlalchemy.base import Base


class Countdown(Base):
    """SQLAlchemy model for countdowns table"""

    __tablename__ = 'countdowns'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    notes: Mapped[str] = mapped_column(Text(), nullable=True)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def __repr__(self):
        return f'Countdown(name={self.name}, notes={self.notes}, due_date={self.due_date}'
