"""Tests for the events seeder."""

from __future__ import annotations

import pytest

from scripts.seed.seeders import events

pytestmark = [pytest.mark.seed, pytest.mark.integration]


class TestEventSeeder:
    def test_creates_events(self, db):
        events.clear(db)
        result = events.seed(db, scale=1)
        assert result.count > 0
