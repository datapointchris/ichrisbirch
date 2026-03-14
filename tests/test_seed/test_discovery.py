"""Tests for model/schema discovery and introspection."""

from __future__ import annotations

from datetime import date
from datetime import datetime

import pytest

from scripts.seed.discovery import LOOKUP_MODELS
from scripts.seed.discovery import SKIP_MODELS
from scripts.seed.discovery import SYSTEM_MODELS
from scripts.seed.discovery import compute_insertion_order
from scripts.seed.discovery import get_seedable_columns

pytestmark = pytest.mark.seed


class TestModelDiscovery:
    def test_discovers_all_seedable_models(self, all_models):
        """All expected models should be discovered from the registry."""
        expected = {
            'Task',
            'Article',
            'AutoTask',
            'Book',
            'Box',
            'BoxItem',
            'Chat',
            'ChatMessage',
            'Countdown',
            'Duration',
            'DurationNote',
            'Event',
            'Habit',
            'HabitCategory',
            'HabitCompleted',
            'MoneyWasted',
        }
        # Lookup models are also discovered
        expected.update(LOOKUP_MODELS)
        for name in expected:
            assert name in all_models, f'{name} not discovered'

    def test_system_models_excluded(self, all_models):
        for name in SYSTEM_MODELS:
            assert name not in all_models

    def test_skip_models_excluded(self, all_models):
        for name in SKIP_MODELS:
            assert name not in all_models

    def test_lookup_tables_identified(self, all_models):
        for name in LOOKUP_MODELS:
            assert all_models[name].is_lookup

    def test_non_lookup_not_flagged(self, all_models):
        assert not all_models['Task'].is_lookup
        assert not all_models['Book'].is_lookup

    def test_task_columns(self, all_models):
        info = all_models['Task']
        cols_by_name = {c.name: c for c in info.columns}

        assert 'name' in cols_by_name
        assert cols_by_name['name'].python_type is str
        assert cols_by_name['name'].max_length == 64

        assert 'category' in cols_by_name
        assert cols_by_name['category'].fk_target == 'task_categories.name'

        assert 'priority' in cols_by_name
        assert cols_by_name['priority'].python_type is int

    def test_book_array_column(self, all_models):
        info = all_models['Book']
        tags_col = next(c for c in info.columns if c.name == 'tags')
        assert tags_col.is_array
        assert tags_col.python_type is list

    def test_article_array_column(self, all_models):
        info = all_models['Article']
        tags_col = next(c for c in info.columns if c.name == 'tags')
        assert tags_col.is_array

    def test_fk_targets_detected(self, all_models):
        task = all_models['Task']
        cat_col = next(c for c in task.columns if c.name == 'category')
        assert cat_col.fk_target == 'task_categories.name'

        autotask = all_models['AutoTask']
        freq_col = next(c for c in autotask.columns if c.name == 'frequency')
        assert 'autotask_frequencies' in freq_col.fk_target

    def test_schema_matching(self, all_models):
        """Create schemas should be matched to models."""
        from ichrisbirch.schemas import TaskCreate

        assert all_models['Task'].create_schema is TaskCreate

        from ichrisbirch.schemas import BookCreate

        assert all_models['Book'].create_schema is BookCreate

    def test_lookup_models_have_no_create_schema_or_have_one(self, all_models):
        """Lookup models may or may not have Create schemas — just verify no crash."""
        for name in LOOKUP_MODELS:
            _ = all_models[name].create_schema

    def test_dependencies_tracked(self, all_models):
        """Models with FKs should track their dependencies."""
        task = all_models['Task']
        assert 'TaskCategory' in task.depends_on

        habit = all_models['Habit']
        assert 'HabitCategory' in habit.depends_on

    def test_box_item_depends_on_box(self, all_models):
        box_item = all_models['BoxItem']
        assert 'Box' in box_item.depends_on

    def test_chat_message_depends_on_chat(self, all_models):
        msg = all_models['ChatMessage']
        assert 'Chat' in msg.depends_on

    def test_datetime_columns(self, all_models):
        event = all_models['Event']
        date_col = next(c for c in event.columns if c.name == 'date')
        assert date_col.python_type is datetime

        countdown = all_models['Countdown']
        due_col = next(c for c in countdown.columns if c.name == 'due_date')
        assert due_col.python_type is date


class TestInsertionOrder:
    def test_parents_before_children(self, all_models):
        order = compute_insertion_order(all_models)
        for name, info in all_models.items():
            if name not in order:
                continue
            idx = order.index(name)
            for dep in info.depends_on:
                if dep in order:
                    assert order.index(dep) < idx, f'{dep} should come before {name}'

    def test_habit_category_before_habit(self, all_models):
        order = compute_insertion_order(all_models)
        if 'HabitCategory' in order and 'Habit' in order:
            assert order.index('HabitCategory') < order.index('Habit')

    def test_box_before_box_item(self, all_models):
        order = compute_insertion_order(all_models)
        if 'Box' in order and 'BoxItem' in order:
            assert order.index('Box') < order.index('BoxItem')

    def test_chat_before_chat_message(self, all_models):
        order = compute_insertion_order(all_models)
        if 'Chat' in order and 'ChatMessage' in order:
            assert order.index('Chat') < order.index('ChatMessage')


class TestSeedableColumns:
    def test_excludes_primary_keys(self, all_models):
        cols = get_seedable_columns(all_models['Task'])
        assert all(not c.is_primary_key for c in cols)

    def test_includes_all_data_columns(self, all_models):
        cols = get_seedable_columns(all_models['Task'])
        names = {c.name for c in cols}
        assert 'name' in names
        assert 'category' in names
        assert 'priority' in names
