import calendar
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta
from typing import Optional

import pendulum


class EasyDate:
    """Create easy to use python date filters."""

    def __init__(self, today: Optional[date] = None, tz='local'):
        self.today: date = today or pendulum.today(tz).date()
        self.tomorrow: date = self.today + timedelta(days=1)
        self.yesterday: date = self.today - timedelta(days=1)
        self.previous_7: date = self.today - timedelta(days=7)
        self.previous_30: date = self.today - timedelta(days=30)
        self._month_days: int = calendar.monthrange(self.today.year, self.today.month)[1]
        self._week_number: int = self.today.isocalendar().week
        self.week_start: date = date.fromisocalendar(self.today.year, self._week_number, 1)
        self.week_end: date = self.week_start + timedelta(days=7)
        self.this_month: date = date(self.today.year, self.today.month, 1)
        self.next_month: date = self.this_month + timedelta(days=self._month_days)
        self.this_year: date = date(self.today.year, 1, 1)
        self.next_year: date = date(self.today.year + 1, 1, 1)

        self.filters: dict[str, tuple[date, date]] = {
            'today': (self.today, self.tomorrow),
            'yesterday': (self.yesterday, self.today),
            'this_week': (self.week_start, self.week_end),
            'last_7': (self.previous_7, self.tomorrow),
            'this_month': (self.this_month, self.next_month),
            'last_30': (self.previous_30, self.tomorrow),
            'this_year': (self.this_year, self.next_year),
        }


class EasyDateTime:
    """Create easy to use python datetime filters."""

    def __init__(self, today: Optional[datetime] = None, tz='local'):
        self.today: datetime = today or pendulum.today(tz)
        self.tomorrow: datetime = self.today + timedelta(days=1)
        self.yesterday: datetime = self.today - timedelta(days=1)
        self.previous_7: datetime = self.today - timedelta(days=7)
        self.previous_30: datetime = self.today - timedelta(days=30)
        self._month_days: int = calendar.monthrange(self.today.year, self.today.month)[1]
        self._week_number: int = self.today.isocalendar().week
        self.week_start: datetime = datetime.combine(
            date.fromisocalendar(self.today.year, self._week_number, 1), time()
        )
        self.week_end: datetime = self.week_start + timedelta(days=7)
        self.this_month: datetime = datetime(self.today.year, self.today.month, 1)
        self.next_month: datetime = self.this_month + timedelta(days=self._month_days)
        self.last_month: datetime = self.this_month - timedelta(days=self._month_days)
        self.this_year: datetime = datetime(self.today.year, 1, 1)
        self.next_year: datetime = datetime(self.this_year.year + 1, 1, 1)
        self.last_year: datetime = datetime(self.this_year.year - 1, 1, 1)

        self.filters: dict[str, tuple[datetime, datetime]] = {
            'today': (self.today, self.tomorrow),
            'yesterday': (self.yesterday, self.today),
            'this_week': (self.week_start, self.week_end),
            'last_7': (self.previous_7, self.tomorrow),
            'this_month': (self.this_month, self.next_month),
            'last_30': (self.previous_30, self.tomorrow),
            'this_year': (self.this_year, self.next_year),
        }
