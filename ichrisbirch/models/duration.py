from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from ichrisbirch.database.base import Base

if TYPE_CHECKING:
    from ichrisbirch.models.duration_note import DurationNote


class Duration(Base):
    __tablename__ = 'durations'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    color: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_notes: Mapped[list[DurationNote]] = relationship(
        back_populates='duration',
        order_by='DurationNote.date',
        cascade='all, delete-orphan',
    )

    def __repr__(self) -> str:
        return f'Duration(id={self.id!r}, name={self.name!r}, start_date={self.start_date!r}, end_date={self.end_date!r})'
