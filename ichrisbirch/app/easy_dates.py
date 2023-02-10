import calendar
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


@dataclass
class EasyDate:
    """Create easy to use python date filters"""

    today: date = date.today()
    tomorrow: date = today + timedelta(days=1)
    yesterday: date = today - timedelta(days=1)
    previous_7: date = today - timedelta(days=7)
    previous_30: date = today - timedelta(days=30)
    _month_days: int = calendar.monthrange(today.year, today.month)[1]
    _week_number: int = today.isocalendar().week
    week_start: date = date.fromisocalendar(today.year, _week_number, 1)
    week_end: date = week_start + timedelta(days=7)
    this_month: date = date(today.year, today.month, 1)
    next_month: date = this_month + timedelta(days=_month_days)
    this_year: date = date(today.year, 1, 1)
    next_year: date = date(today.year + 1, 1, 1)
    year_1900: datetime = datetime(1900, 1, 1)
    year_2100: datetime = datetime(2100, 1, 1)


@dataclass
class EasyDateTime:
    """Create easy to use python datetime filters"""

    today: datetime = datetime.combine(date.today(), time(), tzinfo=ZoneInfo("America/Chicago"))
    tomorrow: datetime = today + timedelta(days=1)
    yesterday: datetime = today - timedelta(days=1)
    previous_7: datetime = today - timedelta(days=7)
    previous_30: datetime = today - timedelta(days=30)
    _month_days: int = calendar.monthrange(today.year, today.month)[1]
    _week_number: int = today.isocalendar().week
    week_start: datetime = datetime.combine(date.fromisocalendar(today.year, _week_number, 1), time())
    week_end: datetime = week_start + timedelta(days=7)
    this_month: datetime = datetime(today.year, today.month, 1)
    next_month: datetime = this_month + timedelta(days=_month_days)
    this_year: datetime = datetime(today.year, 1, 1)
    next_year: datetime = datetime(today.year + 1, 1, 1)
    year_minus_20: datetime = datetime(today.year - 20, 1, 1)
    year_plus_20: datetime = datetime(today.year + 20, 1, 1)
