"""Tests for the autotasks seeder."""

from __future__ import annotations

import pytest

from ichrisbirch.models.autotask import AUTOTASK_FREQUENCIES
from ichrisbirch.models.autotask import AutoTask
from scripts.seed.seeders import autotasks

pytestmark = [pytest.mark.seed, pytest.mark.integration]


class TestAutoTaskSeeder:
    def test_creates_autotasks(self, db):
        autotasks.clear(db)
        result = autotasks.seed(db, scale=1)
        assert result.count == len(autotasks.AUTOTASKS)

    def test_covers_all_frequencies(self, db):
        autotasks.clear(db)
        autotasks.seed(db, scale=1)
        freqs = {a.frequency for a in db.query(AutoTask).all()}
        assert freqs == set(AUTOTASK_FREQUENCIES)

    def test_scale_multiplier(self, db):
        autotasks.clear(db)
        r1 = autotasks.seed(db, scale=1)
        autotasks.clear(db)
        r2 = autotasks.seed(db, scale=2)
        assert r2.count > r1.count
