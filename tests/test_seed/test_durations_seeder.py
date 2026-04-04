"""Tests for the durations seeder."""

from __future__ import annotations

import pytest

from ichrisbirch.models.duration import Duration
from ichrisbirch.models.duration_note import DurationNote
from scripts.seed.seeders import durations

pytestmark = [pytest.mark.seed, pytest.mark.integration]


class TestDurationSeeder:
    def test_notes_reference_valid_durations(self, db):
        durations.clear(db)
        durations.seed(db, scale=1)
        dur_ids = {d.id for d in db.query(Duration).all()}
        note_dur_ids = {n.duration_id for n in db.query(DurationNote).all()}
        assert note_dur_ids.issubset(dur_ids)
