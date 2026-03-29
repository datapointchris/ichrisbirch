"""Tests for the durations seeder."""

from __future__ import annotations

import pytest

from ichrisbirch.models.duration import Duration
from ichrisbirch.models.duration_note import DurationNote
from scripts.seed.seeders import durations

pytestmark = [pytest.mark.seed, pytest.mark.integration]


class TestDurationSeeder:
    def test_creates_durations(self, db):
        durations.clear(db)
        result = durations.seed(db, scale=1)
        count = db.query(Duration).count()
        assert count == len(durations.DURATIONS)
        assert result.count == count

    def test_has_active_and_completed(self, db):
        durations.clear(db)
        durations.seed(db, scale=1)
        all_durations = db.query(Duration).all()
        active = sum(1 for d in all_durations if d.end_date is None)
        completed = sum(1 for d in all_durations if d.end_date is not None)
        assert active >= 1
        assert completed >= 1

    def test_has_notes(self, db):
        durations.clear(db)
        durations.seed(db, scale=1)
        note_count = db.query(DurationNote).count()
        assert note_count >= 1

    def test_notes_reference_valid_durations(self, db):
        durations.clear(db)
        durations.seed(db, scale=1)
        dur_ids = {d.id for d in db.query(Duration).all()}
        note_dur_ids = {n.duration_id for n in db.query(DurationNote).all()}
        assert note_dur_ids.issubset(dur_ids)

    def test_scale_multiplier(self, db):
        durations.clear(db)
        r1 = durations.seed(db, scale=1)
        durations.clear(db)
        r2 = durations.seed(db, scale=2)
        assert r2.count > r1.count
