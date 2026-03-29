"""Tests for the tasks seeder."""

from __future__ import annotations

import pytest

from ichrisbirch.models.task import Task
from scripts.seed.seeders import tasks

pytestmark = [pytest.mark.seed, pytest.mark.integration]


class TestTaskSeeder:
    def test_creates_tasks_for_every_category(self, db):
        tasks.clear(db)
        tasks.seed(db, scale=1)
        cats = {t.category for t in db.query(Task).all()}
        assert cats == set(tasks.TASKS_BY_CATEGORY.keys())

    def test_has_completed_tasks(self, db):
        tasks.clear(db)
        tasks.seed(db, scale=1)
        completed = db.query(Task).filter(Task.complete_date.isnot(None)).count()
        assert completed >= 1

    def test_has_tasks_with_and_without_notes(self, db):
        tasks.clear(db)
        tasks.seed(db, scale=1)
        all_tasks = db.query(Task).all()
        with_notes = sum(1 for t in all_tasks if t.notes)
        without_notes = sum(1 for t in all_tasks if not t.notes)
        assert with_notes >= 1
        assert without_notes >= 1

    def test_scale_multiplier(self, db):
        tasks.clear(db)
        r1 = tasks.seed(db, scale=1)
        tasks.clear(db)
        r2 = tasks.seed(db, scale=2)
        assert r2.count > r1.count

    def test_returns_seed_result(self, db):
        tasks.clear(db)
        result = tasks.seed(db, scale=1)
        assert result.model == 'Task'
        assert result.count > 0
        assert 'categories' in result.details
