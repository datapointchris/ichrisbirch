"""Tests for the money wasted seeder."""

from __future__ import annotations

import pytest

from ichrisbirch.models.money_wasted import MoneyWasted
from scripts.seed.seeders import money_wasted

pytestmark = [pytest.mark.seed, pytest.mark.integration]


class TestMoneyWastedSeeder:
    def test_creates_entries(self, db):
        money_wasted.clear(db)
        result = money_wasted.seed(db, scale=1)
        assert result.count == len(money_wasted.ITEMS)

    def test_has_varied_amounts(self, db):
        money_wasted.clear(db)
        money_wasted.seed(db, scale=1)
        amounts = {e.amount for e in db.query(MoneyWasted).all()}
        assert len(amounts) > 1

    def test_has_entries_with_and_without_purchase_date(self, db):
        money_wasted.clear(db)
        money_wasted.seed(db, scale=1)
        all_entries = db.query(MoneyWasted).all()
        with_date = sum(1 for e in all_entries if e.date_purchased)
        without_date = sum(1 for e in all_entries if not e.date_purchased)
        assert with_date >= 1
        assert without_date >= 1

    def test_scale_multiplier(self, db):
        money_wasted.clear(db)
        r1 = money_wasted.seed(db, scale=1)
        money_wasted.clear(db)
        r2 = money_wasted.seed(db, scale=2)
        assert r2.count > r1.count
