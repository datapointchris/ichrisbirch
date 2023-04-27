import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from ichrisbirch.db.sqlalchemy.base import Base


class TaskCategory(enum.Enum):
    Automotive = 'Automotive'
    Home = 'Home'
    Work = 'Work'
    Chore = 'Chore'
    Kitchen = 'Kitchen'
    Dingo = 'Dingo'
    Learn = 'Learn'
    Research = 'Research'
    Computer = 'Computer'
    Financial = 'Financial'
    Purchase = 'Purchase'


class Task(Base):
    """SQLAlchemy model for tasks table"""

    __tablename__ = 'tasks'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    notes: Mapped[str] = mapped_column(Text(), nullable=True)
    category: Mapped[Enum] = mapped_column(Enum(TaskCategory))
    priority: Mapped[int] = mapped_column(Integer)
    add_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    complete_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f''''Task(name = {self.name}, priority = {self.priority}, category = {self.category},
            add_date = {self.add_date}, complete_date = {self.complete_date})'''
