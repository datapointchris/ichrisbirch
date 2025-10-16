from typing import TYPE_CHECKING

from sqlalchemy import Boolean
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from ichrisbirch.database.base import Base

if TYPE_CHECKING:
    from ichrisbirch.models.habitcategory import HabitCategory


class Habit(Base):
    __table_args__ = {'schema': 'habits'}
    __tablename__ = 'habits'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('habits.categories.id'), nullable=False)
    category: Mapped['HabitCategory'] = relationship('HabitCategory', back_populates='habits')
    is_current: Mapped[bool] = mapped_column(Boolean)

    def __repr__(self):
        return f'Habit(name={self.name!r}, category_id={self.category_id!r}, is_current={self.is_current!r})'
