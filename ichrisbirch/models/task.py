from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from ichrisbirch.database.base import Base

TASK_CATEGORIES = [
    'Automotive',
    'Chore',
    'Computer',
    'Dingo',
    'Financial',
    'Home',
    'Kitchen',
    'Learn',
    'Personal',
    'Purchase',
    'Research',
    'Work',
]


class TaskCategory(Base):
    """Lookup table for valid task categories, replacing PostgreSQL ENUM type."""

    __tablename__ = 'task_categories'
    name: Mapped[str] = mapped_column(Text, primary_key=True)


class Task(Base):
    __tablename__ = 'tasks'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(Text, ForeignKey('task_categories.name'), nullable=False)
    priority: Mapped[int] = mapped_column(Integer)
    add_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    complete_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"""Task(name = {self.name}, priority = {self.priority}, category = {self.category},
            add_date = {self.add_date}, complete_date = {self.complete_date})"""
