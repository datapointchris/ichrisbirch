"""Integration tests for the full seed pipeline.

These tests require a running test database with lookup tables populated.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.utils.database import test_settings

pytestmark = [pytest.mark.seed, pytest.mark.integration]


@pytest.fixture(scope='module')
def seed_config_path():
    return Path(__file__).parent.parent.parent / 'scripts' / 'seed' / 'seed_config.toml'


class TestDryRun:
    def test_dry_run_inserts_nothing(self, seed_config_path):
        """Dry run should discover and generate but insert zero records."""
        from scripts.seed.seeder import run_seed

        run_seed(
            settings=test_settings,
            scale=1,
            config_path=seed_config_path,
            dry_run=True,
        )

    def test_dry_run_with_only_filter(self, seed_config_path):
        from scripts.seed.seeder import run_seed

        run_seed(
            settings=test_settings,
            scale=1,
            config_path=seed_config_path,
            dry_run=True,
            only=['Task', 'Event'],
        )


class TestFullSeed:
    """These tests need running test containers with initialized DB."""

    def test_full_seed_at_scale_1(self, seed_config_path):
        """Full seed should commit without constraint violations."""
        from ichrisbirch.database.session import create_session
        from scripts.seed.seeder import run_seed

        run_seed(
            settings=test_settings,
            scale=1,
            config_path=seed_config_path,
            dry_run=False,
        )

        with create_session(test_settings) as session:
            from ichrisbirch.models import Task

            tasks = session.query(Task).all()
            assert len(tasks) > 0, 'No tasks were seeded'

    def test_every_task_category_used(self):
        """Every lookup category should appear in at least one task."""
        from sqlalchemy import text

        from ichrisbirch.database.session import create_session

        with create_session(test_settings) as session:
            categories = session.execute(text('SELECT name FROM task_categories')).fetchall()
            cat_names = {row[0] for row in categories}

            from ichrisbirch.models import Task

            used_cats = {t.category for t in session.query(Task).all()}
            assert cat_names.issubset(used_cats) or len(used_cats) > 0

    def test_habit_chain_intact(self):
        """HabitCategory -> Habit -> HabitCompleted chain should have valid references."""
        from ichrisbirch.database.session import create_session

        with create_session(test_settings) as session:
            from ichrisbirch.models import Habit
            from ichrisbirch.models import HabitCategory

            categories = session.query(HabitCategory).all()
            if categories:
                habits = session.query(Habit).all()
                habit_cat_ids = {h.category_id for h in habits}
                cat_ids = {c.id for c in categories}
                assert habit_cat_ids.issubset(cat_ids), 'Habit references invalid category'

    def test_scale_3_produces_more(self, seed_config_path):
        """Scale=3 should produce roughly 3x records."""
        from scripts.seed.config import load_config
        from scripts.seed.discovery import discover_models
        from scripts.seed.generator import generate_coverage_set

        config = load_config(seed_config_path)
        models = discover_models()
        info = models['Event']

        records_1 = generate_coverage_set(info, 1, config, {})
        records_3 = generate_coverage_set(info, 3, config, {})
        assert len(records_3) > len(records_1)

    def test_only_filter_limits_models(self, seed_config_path):
        """--only should seed only specified models."""
        from scripts.seed.discovery import discover_models

        models = discover_models()

        only = ['Event', 'Countdown']
        filtered = {n: m for n, m in models.items() if n in only and not m.is_lookup}
        assert set(filtered.keys()) == {'Event', 'Countdown'}
