from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Identity
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from ichrisbirch.database.base import Base


class AutoFun(Base):
    __tablename__ = 'autofun'
    id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    completed_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    added_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f'AutoFun(name={self.name}, is_completed={self.is_completed})'


class AutoFunActiveTask(Base):
    """Junction table tracking which AutoFun items are currently on the task list."""

    __tablename__ = 'autofun_active_tasks'
    fun_item_id: Mapped[int] = mapped_column(Integer, ForeignKey('autofun.id'), primary_key=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey('tasks.id'), primary_key=True)
