from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from ichrisbirch.database.sqlalchemy.base import Base

if TYPE_CHECKING:
    from ichrisbirch.models.habitcategory import HabitCategory


class HabitCompleted(Base):
    __table_args__ = {'schema': 'habits'}
    __tablename__ = 'completed'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('habits.categories.id'), nullable=False)
    category: Mapped['HabitCategory'] = relationship('HabitCategory', back_populates='completed_habits')
    complete_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def __repr__(self):
        return (
            f'HabitCompleted(name={self.name!r}, '
            f'category_id={self.category_id!r}, '
            f'complete_date={self.complete_date!r})'
        )
