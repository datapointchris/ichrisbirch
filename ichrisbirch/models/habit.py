from datetime import datetime

from sqlalchemy import DateTime, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from ichrisbirch.database.sqlalchemy.base import Base


class Habit(Base):
    __table_args__ = {'schema': 'habits'}
    __tablename__ = 'habits'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('habits.categories.id'), nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean)

    def __repr__(self):
        return f'Habit(name={self.name!r}, category_id={self.category_id!r}, is_current={self.is_current!r})'


class HabitCategory(Base):
    __table_args__ = {'schema': 'habits'}
    __tablename__ = 'categories'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    def __repr__(self):
        return f'Category(name={self.name!r})'


class HabitCompleted(Base):
    __table_args__ = {'schema': 'habits'}
    __tablename__ = 'completed'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('habits.categories.id'), nullable=False)
    complete_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def __repr__(self):
        return f'HabitCompleted(name={self.name!r}, category_id={self.category_id!r}, complete_date={self.complete_date!r})'
