from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from ichrisbirch.database.base import Base

if TYPE_CHECKING:
    from ichrisbirch.models.duration import Duration


class DurationNote(Base):
    __tablename__ = 'duration_notes'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    duration_id: Mapped[int] = mapped_column(ForeignKey('durations.id', ondelete='CASCADE'), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    duration: Mapped['Duration'] = relationship(back_populates='duration_notes')

    def __repr__(self) -> str:
        return f'DurationNote(id={self.id!r}, duration_id={self.duration_id!r}, date={self.date!r})'
