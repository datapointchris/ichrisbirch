"""Tests for the habits seeder."""

from __future__ import annotations

import pytest

from ichrisbirch.models.habit import Habit
from ichrisbirch.models.habitcategory import HabitCategory
from ichrisbirch.models.habitcompleted import HabitCompleted
from scripts.seed.seeders import habits

pytestmark = [pytest.mark.seed, pytest.mark.integration]


class TestHabitSeeder:
    def test_creates_all_categories(self, db):
        habits.clear(db)
        habits.seed(db, scale=1)
        cats = db.query(HabitCategory).all()
        assert len(cats) == len(habits.CATEGORIES)

    def test_habits_reference_valid_categories(self, db):
        habits.clear(db)
        habits.seed(db, scale=1)
        cat_ids = {c.id for c in db.query(HabitCategory).all()}
        habit_cat_ids = {h.category_id for h in db.query(Habit).all()}
        assert habit_cat_ids.issubset(cat_ids)

    def test_completions_reference_valid_categories(self, db):
        habits.clear(db)
        habits.seed(db, scale=1)
        cat_ids = {c.id for c in db.query(HabitCategory).all()}
        comp_cat_ids = {c.category_id for c in db.query(HabitCompleted).all()}
        assert comp_cat_ids.issubset(cat_ids)
