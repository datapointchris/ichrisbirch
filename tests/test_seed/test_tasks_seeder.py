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
