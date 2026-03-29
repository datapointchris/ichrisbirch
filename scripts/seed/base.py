"""Shared types and helpers for the seed system."""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import UTC
from datetime import date
from datetime import datetime
from datetime import timedelta

from faker import Faker

fake = Faker()


@dataclass
class SeedResult:
    model: str
    count: int
    details: str = ''


def random_past_date(days_back: int = 365) -> date:
    """Random date in the past."""
    return date.today() - timedelta(days=random.randint(1, days_back))


def random_past_datetime(days_back: int = 365) -> datetime:
    """Random timezone-aware datetime in the past."""
    return datetime.now(UTC) - timedelta(days=random.randint(1, days_back))


def random_future_date(days_ahead: int = 365) -> date:
    """Random date in the future."""
    return date.today() + timedelta(days=random.randint(1, days_ahead))
