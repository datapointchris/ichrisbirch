"""Integration tests for the seed orchestrator."""

from __future__ import annotations

import pytest

from tests.utils.database import test_settings

pytestmark = [pytest.mark.seed, pytest.mark.integration]


class TestDryRun:
    def test_dry_run_returns_empty(self):
        from scripts.seed.run import run_seed

        results = run_seed(settings=test_settings, scale=1, dry_run=True)
        assert results == []

    def test_dry_run_with_only_filter(self):
        from scripts.seed.run import run_seed

        results = run_seed(settings=test_settings, scale=1, dry_run=True, only=['tasks', 'events'])
        assert results == []


class TestFullSeed:
    """Full seed integration — requires running test containers with initialized DB."""

    def test_full_seed_no_constraint_violations(self):
        from scripts.seed.run import run_seed

        results = run_seed(settings=test_settings, scale=1)
        assert len(results) > 0

    def test_every_seeder_produced_records(self):
        from scripts.seed.run import run_seed

        results = run_seed(settings=test_settings, scale=1)
        for result in results:
            assert result.count > 0, f'{result.model} seeder produced 0 records'

    def test_only_filter_limits_seeders(self):
        from scripts.seed.run import run_seed

        results = run_seed(settings=test_settings, scale=1, only=['tasks', 'countdowns'])
        models = {r.model for r in results}
        assert 'Task' in models
        assert 'Countdown' in models
        assert len(results) == 2
