from datetime import date
from datetime import datetime
from zoneinfo import ZoneInfo

import pendulum
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Identity
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from ichrisbirch.database.base import Base

AUTOTASK_FREQUENCIES = [
    'Biweekly',
    'Daily',
    'Monthly',
    'Quarterly',
    'Semiannually',
    'Weekly',
    'Yearly',
]


class AutoTaskFrequency(Base):
    """Lookup table for valid autotask frequencies, replacing PostgreSQL ENUM type."""

    __tablename__ = 'autotask_frequencies'
    name: Mapped[str] = mapped_column(Text, primary_key=True)


FREQUENCY_DURATIONS = {
    'Daily': pendulum.duration(days=1),
    'Weekly': pendulum.duration(weeks=1),
    'Biweekly': pendulum.duration(weeks=2),
    'Monthly': pendulum.duration(months=1),
    'Quarterly': pendulum.duration(months=3),
    'Semiannually': pendulum.duration(months=6),
    'Yearly': pendulum.duration(years=1),
}


def frequency_to_duration(frequency: str) -> pendulum.Duration:
    """Converts a frequency string to a pendulum.Duration object."""
    if not (delta := FREQUENCY_DURATIONS.get(frequency)):
        raise ValueError(f'Invalid frequency: {frequency}')
    return delta


class AutoTask(Base):
    __tablename__ = 'autotasks'
    id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(Text, ForeignKey('task_categories.name'), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    max_concurrent: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    frequency: Mapped[str] = mapped_column(Text, ForeignKey('autotask_frequencies.name'), nullable=False)
    first_run_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_run_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    run_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def __repr__(self):
        return f"""AutoTask(name = {self.name}, priority = {self.priority}, category = {self.category},
                    frequency = {self.frequency}, max_concurrent = {self.max_concurrent},
                    first_run_date = {self.first_run_date}, last_run_date = {self.last_run_date},
                    run_count = {self.run_count})"""

    def next_run_day(self, zone: ZoneInfo) -> date:
        """The first due day after the last run, counted from the first run's day in `zone`.

        Each due day is the first run's day plus a whole number of steps, and
        pendulum clamps each sum from that day. So a template first run on the
        31st is due on February 28 and then March 31. Stepping from the last run
        would keep the 28th for good, and a run held back at `max_concurrent`
        would move every later one.

        The days are pendulum Dates because a month added to a stdlib date is 30
        days, and a monthly template would then fall five days earlier every year.
        """
        first_day = self.first_run_date.astimezone(zone).date()
        last_day = self.last_run_date.astimezone(zone).date()
        anchor = pendulum.Date(first_day.year, first_day.month, first_day.day)
        step = frequency_to_duration(self.frequency)
        steps = 0
        while (due := anchor + step * steps) <= last_day:
            steps += 1
        return due

    def is_due_on(self, day: date, zone: ZoneInfo) -> bool:
        return self.next_run_day(zone) <= day
