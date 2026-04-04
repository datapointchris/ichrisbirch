"""Tests for the countdowns seeder."""

from __future__ import annotations

import pytest

from scripts.seed.seeders import countdowns

pytestmark = [pytest.mark.seed, pytest.mark.integration]


class TestCountdownSeeder:
    def test_creates_countdowns(self, db):
        countdowns.clear(db)
        result = countdowns.seed(db, scale=1)
        assert result.count > 0
