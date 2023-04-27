import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from ichrisbirch.db.sqlalchemy.base import Base
from ichrisbirch.models.task import TaskCategory


class TaskFrequency(enum.Enum):
    Daily = 'Daily'
    Weekly = 'Weekly'
    Biweekly = 'Biweekly'
    Monthly = 'Monthly'
    Quarterly = 'Quarterly'
    Semiannual = 'Semiannual'
    Yearly = 'Yearly'


class AutoTask(Base):
    """SQLAlchemy model for tasks table"""

    __tablename__ = 'autotasks'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    notes: Mapped[str] = mapped_column(Text(), nullable=True)
    category: Mapped[Enum] = mapped_column(Enum(TaskCategory))
    priority: Mapped[int] = mapped_column(Integer)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_run_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    frequency: Mapped[Optional[datetime]] = mapped_column(Enum(TaskFrequency))

    def __repr__(self):
        return f''''AutoTask(name = {self.name}, priority = {self.priority}, category = {self.category},
            start_date = {self.start_date}, last_run_date = {self.last_run_date}, frequency = {self.frequency})'''
