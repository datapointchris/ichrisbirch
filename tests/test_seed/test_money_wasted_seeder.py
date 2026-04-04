"""Tests for the money wasted seeder."""

from __future__ import annotations

import pytest

from scripts.seed.seeders import money_wasted

pytestmark = [pytest.mark.seed, pytest.mark.integration]


class TestMoneyWastedSeeder:
    def test_creates_entries(self, db):
        money_wasted.clear(db)
        result = money_wasted.seed(db, scale=1)
        assert result.count > 0
