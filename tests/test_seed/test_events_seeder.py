"""Tests for the events seeder."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime

import pytest

from ichrisbirch.models.event import Event
from scripts.seed.seeders import events

pytestmark = [pytest.mark.seed, pytest.mark.integration]


class TestEventSeeder:
    def test_creates_events(self, db):
        events.clear(db)
        result = events.seed(db, scale=1)
        assert result.count == len(events.EVENTS)

    def test_has_past_and_future_events(self, db):
        events.clear(db)
        events.seed(db, scale=1)
        now = datetime.now(UTC)
        all_events = db.query(Event).all()
        past = sum(1 for e in all_events if e.date < now)
        future = sum(1 for e in all_events if e.date >= now)
        assert past >= 1
        assert future >= 1

    def test_has_attending_and_not(self, db):
        events.clear(db)
        events.seed(db, scale=1)
        all_events = db.query(Event).all()
        attending = sum(1 for e in all_events if e.attending)
        not_attending = sum(1 for e in all_events if not e.attending)
        assert attending >= 1
        assert not_attending >= 1

    def test_scale_multiplier(self, db):
        events.clear(db)
        r1 = events.seed(db, scale=1)
        events.clear(db)
        r2 = events.seed(db, scale=2)
        assert r2.count > r1.count
