"""Shared types and helpers for the seed system."""

from __future__ import annotations

import datetime as dt
import random
from dataclasses import dataclass

from faker import Faker

fake = Faker()


@dataclass
class SeedResult:
    model: str
    count: int
    details: str = ''


def random_past_date(days_back: int = 365) -> dt.date:
    """Random date in the past."""
    return dt.date.today() - dt.timedelta(days=random.randint(1, days_back))


def random_past_datetime(days_back: int = 365) -> dt.datetime:
    """Random timezone-aware datetime in the past."""
    return dt.datetime.now(dt.UTC) - dt.timedelta(days=random.randint(1, days_back))


def random_future_date(days_ahead: int = 365) -> dt.date:
    """Random date in the future."""
    return dt.date.today() + dt.timedelta(days=random.randint(1, days_ahead))
