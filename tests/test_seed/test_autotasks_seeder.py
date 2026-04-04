"""Tests for the autotasks seeder."""

from __future__ import annotations

import pytest

from ichrisbirch.models.autotask import AUTOTASK_FREQUENCIES
from ichrisbirch.models.autotask import AutoTask
from scripts.seed.seeders import autotasks

pytestmark = [pytest.mark.seed, pytest.mark.integration]


class TestAutoTaskSeeder:
    def test_covers_all_frequencies(self, db):
        autotasks.clear(db)
        autotasks.seed(db, scale=1)
        freqs = {a.frequency for a in db.query(AutoTask).all()}
        assert freqs == set(AUTOTASK_FREQUENCIES)
