import enum
from datetime import date
from datetime import datetime

from pendulum import duration
from pendulum.duration import Duration
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.sql import func

from ichrisbirch.database.sqlalchemy.base import Base
from ichrisbirch.models.task import TaskCategory


class TaskFrequency(enum.Enum):
    # Change to enum.StrEnum when no longer < 3.11
    Daily = 'Daily'
    Weekly = 'Weekly'
    Biweekly = 'Biweekly'
    Monthly = 'Monthly'
    Quarterly = 'Quarterly'
    Semiannual = 'Semiannual'
    Yearly = 'Yearly'


def frequency_to_duration(frequency: TaskFrequency | str) -> Duration:
    """Converts a frequency string or TaskFrequency to a pendulum.Duration object."""

    if isinstance(frequency, str):
        frequency = TaskFrequency(frequency.capitalize())
    if not (
        delta := {
            TaskFrequency.Daily: duration(days=1),
            TaskFrequency.Weekly: duration(weeks=1),
            TaskFrequency.Biweekly: duration(weeks=2),
            TaskFrequency.Monthly: duration(months=1),
            TaskFrequency.Quarterly: duration(months=3),
            TaskFrequency.Semiannual: duration(months=6),
            TaskFrequency.Yearly: duration(years=1),
        }.get(frequency)
    ):
        raise ValueError(f'Invalid frequency: {frequency}')
    return delta


class AutoTask(Base):
    """SQLAlchemy model for tasks table."""

    __tablename__ = 'autotasks'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    category: Mapped[TaskCategory] = mapped_column(Enum(TaskCategory), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    frequency: Mapped[TaskFrequency] = mapped_column(Enum(TaskFrequency), nullable=False)
    first_run_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_run_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    run_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0')

    def __repr__(self):
        return f'''AutoTask(name = {self.name}, priority = {self.priority}, category = {self.category},
                    frequency = {self.frequency}, first_run_date = {self.first_run_date},
                    last_run_date = {self.last_run_date}, run_count = {self.run_count})'''

    @property
    def next_run_date(self) -> date:
        """Returns the next date the task should be run."""
        return self.last_run_date.date() + frequency_to_duration(self.frequency)

    @property
    def should_run_today(self):
        """Returns true if the task should be run today."""
        return self.next_run_date <= datetime.now().date() and self.last_run_date.date() != datetime.now().date()
