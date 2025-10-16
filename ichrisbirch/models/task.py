import enum
from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from ichrisbirch.database.base import Base


class TaskCategory(enum.Enum):
    Automotive = 'Automotive'
    Chore = 'Chore'
    Computer = 'Computer'
    Dingo = 'Dingo'
    Financial = 'Financial'
    Home = 'Home'
    Kitchen = 'Kitchen'
    Learn = 'Learn'
    Personal = 'Personal'
    Purchase = 'Purchase'
    Research = 'Research'
    Work = 'Work'


class Task(Base):
    __tablename__ = 'tasks'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    category: Mapped[TaskCategory] = mapped_column(Enum(TaskCategory), nullable=False)
    priority: Mapped[int] = mapped_column(Integer)
    add_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    complete_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"""Task(name = {self.name}, priority = {self.priority}, category = {self.category},
            add_date = {self.add_date}, complete_date = {self.complete_date})"""
