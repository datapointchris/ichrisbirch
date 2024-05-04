from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from ichrisbirch.database.sqlalchemy.base import Base


class HabitCategory(Base):
    __table_args__ = {'schema': 'habits'}
    __tablename__ = 'categories'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean)

    def __repr__(self):
        return f'Category(name={self.name!r})'


class Habit(Base):
    __table_args__ = {'schema': 'habits'}
    __tablename__ = 'habits'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('habits.categories.id'), nullable=False)
    category: Mapped[HabitCategory] = relationship('HabitCategory', backref='habits')
    is_current: Mapped[bool] = mapped_column(Boolean)

    def __repr__(self):
        return f'Habit(name={self.name!r}, category_id={self.category_id!r}, is_current={self.is_current!r})'


class HabitCompleted(Base):
    __table_args__ = {'schema': 'habits'}
    __tablename__ = 'completed'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('habits.categories.id'), nullable=False)
    category: Mapped[HabitCategory] = relationship('HabitCategory', backref='completed_habits')
    complete_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def __repr__(self):
        return (
            f'HabitCompleted(name={self.name!r}, '
            f'category_id={self.category_id!r}, '
            f'complete_date={self.complete_date!r})'
        )
