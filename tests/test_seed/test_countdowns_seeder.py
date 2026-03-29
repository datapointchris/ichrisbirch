"""Tests for the countdowns seeder."""

from __future__ import annotations

from datetime import date

import pytest

from ichrisbirch.models.countdown import Countdown
from scripts.seed.seeders import countdowns

pytestmark = [pytest.mark.seed, pytest.mark.integration]


class TestCountdownSeeder:
    def test_creates_countdowns(self, db):
        countdowns.clear(db)
        result = countdowns.seed(db, scale=1)
        assert result.count == len(countdowns.COUNTDOWNS)

    def test_has_near_and_far_due_dates(self, db):
        countdowns.clear(db)
        countdowns.seed(db, scale=1)
        all_countdowns = db.query(Countdown).all()
        today = date.today()
        near = sum(1 for c in all_countdowns if (c.due_date - today).days <= 30)
        far = sum(1 for c in all_countdowns if (c.due_date - today).days > 30)
        assert near >= 1
        assert far >= 1

    def test_scale_multiplier(self, db):
        countdowns.clear(db)
        r1 = countdowns.seed(db, scale=1)
        countdowns.clear(db)
        r2 = countdowns.seed(db, scale=2)
        assert r2.count > r1.count
