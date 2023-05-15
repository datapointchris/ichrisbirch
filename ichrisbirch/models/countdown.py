from datetime import date

from sqlalchemy import Date, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ichrisbirch.db.sqlalchemy.base import Base


class Countdown(Base):
    """SQLAlchemy model for countdowns table"""

    __tablename__ = 'countdowns'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    notes: Mapped[str] = mapped_column(Text(), nullable=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)

    def __repr__(self):
        return f'Countdown(name={self.name}, notes={self.notes}, due_date={self.due_date}'
