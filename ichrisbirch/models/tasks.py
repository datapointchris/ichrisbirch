import enum

from sqlalchemy import Column, DateTime, Enum, Integer, String, Text
from sqlalchemy.sql import func

from ichrisbirch.db.sqlalchemy.base import Base


class TaskCategory(enum.Enum):
    Automotive = 'Automotive'
    Home = 'Home'
    Chore = 'Chore'
    Dingo = 'Dingo'
    Research = 'Research'
    Learn = 'Learn'
    Computer = 'Computer'
    Financial = 'Financial'


class Task(Base):
    """SQLAlchemy model for tasks table"""

    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    notes = Column(Text())
    category = Column(Enum(TaskCategory))
    priority = Column(Integer, nullable=False)
    add_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    complete_date = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f''''Task(name = {self.name}, priority = {self.priority}, category = {self.category},
            add_date = {self.add_date}, complete_date = {self.complete_date})'''

    @property
    def days_to_complete(self) -> int:
        """Calculate days it took to complete task"""
        return (self.complete_date - self.add_date).days + 1

    @property
    def weeks_to_complete(self) -> str:
        """Calculate weeks and days it took to complete task"""
        weeks, days = divmod(self.days_to_complete, 7)
        return f'{weeks} weeks, {days} days'
