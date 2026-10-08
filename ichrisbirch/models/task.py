from datetime import UTC
from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import CheckConstraint
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Identity
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy import text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from ichrisbirch.database.base import Base

# Days a new task in the category gets before it sorts as due. Seeds
# `task_categories.window_days` for a new database. The deployed values are
# tuned through the API.
TASK_CATEGORY_WINDOW_DAYS = {
    'Automotive': 45,
    'Chore': 30,
    'Computer': 90,
    'Dingo': 7,
    'Financial': 30,
    'Home': 60,
    'Kitchen': 30,
    'Learn': 180,
    'Personal': 60,
    'Purchase': 30,
    'Research': 180,
    'Work': 60,
}

TASK_CATEGORIES = sorted(TASK_CATEGORY_WINDOW_DAYS)


class TaskCategory(Base):
    """Lookup table for valid task categories, replacing PostgreSQL ENUM type."""

    __tablename__ = 'task_categories'
    name: Mapped[str] = mapped_column(Text, primary_key=True)
    window_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('60'))

    __table_args__ = (CheckConstraint('window_days >= 1', name='window_days_positive'),)


class Task(Base):
    """A task in the to-do list.

    Open tasks are read in `(pinned DESC, rank_at ASC, add_date ASC)` order.
    `rank_at` is when the task should reach the top, set to creation plus
    `window_days` and moved by snooze and drag. It is never shown as a due date.

    `priority` is a positional rank that nothing reads or writes. Rows keep the
    value they hold.

    A task is open, completed (`complete_date`) or dropped (`drop_date`), never
    both closed states at once. Only an open task is pinned, and only a dropped
    task has a `drop_reason`.
    """

    __tablename__ = 'tasks'
    id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(Text, ForeignKey('task_categories.name'), nullable=False)
    priority: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # The server defaults exist for the release serving while the migration
    # runs, which inserts without these columns. This code always sets them.
    rank_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now() + interval '30 days'"))
    window_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('30'))
    pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text('false'))
    autotask_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('autotasks.id', ondelete='SET NULL'), nullable=True)
    add_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    complete_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    drop_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    drop_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint('window_days >= 1', name='window_days_positive'),
        CheckConstraint('complete_date IS NULL OR drop_date IS NULL', name='one_closed_state'),
        CheckConstraint('NOT pinned OR (complete_date IS NULL AND drop_date IS NULL)', name='pinned_only_open'),
        CheckConstraint('drop_reason IS NULL OR drop_date IS NOT NULL', name='drop_reason_needs_drop_date'),
    )

    def __repr__(self):
        return f"""Task(name = {self.name}, category = {self.category}, rank_at = {self.rank_at},
            pinned = {self.pinned}, add_date = {self.add_date}, complete_date = {self.complete_date},
            drop_date = {self.drop_date})"""
