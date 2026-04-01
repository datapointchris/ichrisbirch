from typing import TYPE_CHECKING

from sqlalchemy import Boolean
from sqlalchemy import Identity
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from ichrisbirch.database.base import Base

if TYPE_CHECKING:
    from ichrisbirch.models.habit import Habit
    from ichrisbirch.models.habitcompleted import HabitCompleted


class HabitCategory(Base):
    __table_args__ = {'schema': 'habits'}
    __tablename__ = 'categories'
    id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    habits: Mapped[list[Habit]] = relationship('Habit', back_populates='category')
    completed_habits: Mapped[list[HabitCompleted]] = relationship('HabitCompleted', back_populates='category')
    is_current: Mapped[bool] = mapped_column(Boolean)

    def __repr__(self):
        return f'Category(name={self.name!r})'
