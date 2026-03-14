"""Tests for data generation engine."""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from scripts.seed.config import SeedConfig
from scripts.seed.generator import generate_coverage_set
from scripts.seed.generator import generate_value

pytestmark = pytest.mark.seed


# Sample FK caches for testing
TASK_FK_CACHE = {
    'task_categories.name': [
        'Automotive',
        'Chore',
        'Computer',
        'Dingo',
        'Financial',
        'Home',
        'Kitchen',
        'Learn',
        'Personal',
        'Purchase',
        'Research',
        'Work',
    ],
}

AUTOTASK_FK_CACHE = TASK_FK_CACHE | {
    'autotask_frequencies.name': [
        'Biweekly',
        'Daily',
        'Monthly',
        'Quarterly',
        'Semiannually',
        'Weekly',
        'Yearly',
    ],
}

BOX_FK_CACHE = {
    'box_packing.box_sizes.name': [
        'Bag',
        'Book',
        'Large',
        'Medium',
        'Misc',
        'Monitor',
        'Sixteen',
        'Small',
        'UhaulSmall',
    ],
}


class TestGenerateValue:
    def test_config_pool_override(self, all_models, seed_config):
        col = next(c for c in all_models['Task'].columns if c.name == 'name')
        value = generate_value(col, seed_config, 'Task', {}, {})
        pool = seed_config.get_pool('Task', 'name')
        assert value in pool

    def test_fk_values_cycle(self, all_models):
        col = next(c for c in all_models['Task'].columns if c.name == 'category')
        config = SeedConfig()
        counters: dict[str, int] = {}
        values = [generate_value(col, config, 'Task', TASK_FK_CACHE, counters) for _ in range(24)]
        assert set(values) == set(TASK_FK_CACHE['task_categories.name'])

    def test_name_heuristic_for_url(self, all_models):
        col = next(c for c in all_models['Event'].columns if c.name == 'url')
        config = SeedConfig()
        value = generate_value(col, config, 'Event', {}, {})
        assert isinstance(value, str)

    def test_type_fallback(self, all_models):
        col = next(c for c in all_models['Task'].columns if c.name == 'priority')
        config = SeedConfig()
        value = generate_value(col, config, 'Task', {}, {})
        assert isinstance(value, int)

    def test_max_length_respected(self, all_models):
        col = next(c for c in all_models['Task'].columns if c.name == 'name')
        config = SeedConfig()
        for _ in range(50):
            value = generate_value(col, config, 'Task', {}, {})
            assert len(value) <= 64


class TestSchemaValidation:
    """Generated records must pass their Pydantic Create schema validation."""

    def _validate_model(self, model_name: str, all_models, seed_config, fk_cache: dict):
        info = all_models[model_name]
        records = generate_coverage_set(info, 1, seed_config, fk_cache)
        assert records, f'No records generated for {model_name}'
        for i, record in enumerate(records):
            if info.create_schema:
                try:
                    info.create_schema(**record)
                except ValidationError as e:
                    pytest.fail(f'{model_name} record {i} failed validation: {e}\nRecord: {record}')

    def test_task_records_valid(self, all_models, seed_config):
        self._validate_model('Task', all_models, seed_config, TASK_FK_CACHE)

    def test_event_records_valid(self, all_models, seed_config):
        self._validate_model('Event', all_models, seed_config, {})

    def test_book_records_valid(self, all_models, seed_config):
        self._validate_model('Book', all_models, seed_config, {})

    def test_article_records_valid(self, all_models, seed_config):
        self._validate_model('Article', all_models, seed_config, {})

    def test_countdown_records_valid(self, all_models, seed_config):
        self._validate_model('Countdown', all_models, seed_config, {})

    def test_autotask_records_valid(self, all_models, seed_config):
        self._validate_model('AutoTask', all_models, seed_config, AUTOTASK_FK_CACHE)

    def test_money_wasted_records_valid(self, all_models, seed_config):
        self._validate_model('MoneyWasted', all_models, seed_config, {})

    def test_duration_records_valid(self, all_models, seed_config):
        self._validate_model('Duration', all_models, seed_config, {})

    def test_chat_records_valid(self, all_models, seed_config):
        self._validate_model('Chat', all_models, seed_config, {})

    def test_box_records_valid(self, all_models, seed_config):
        self._validate_model('Box', all_models, seed_config, BOX_FK_CACHE)

    def test_habit_category_records_valid(self, all_models, seed_config):
        self._validate_model('HabitCategory', all_models, seed_config, {})

    def test_habit_records_valid(self, all_models, seed_config):
        fk_cache = {'habits.categories.id': [1, 2, 3, 4, 5]}
        self._validate_model('Habit', all_models, seed_config, fk_cache)

    def test_habit_completed_records_valid(self, all_models, seed_config):
        fk_cache = {'habits.categories.id': [1, 2, 3, 4, 5]}
        self._validate_model('HabitCompleted', all_models, seed_config, fk_cache)


class TestCoverageProperties:
    def test_boolean_coverage_for_box(self, all_models, seed_config):
        """Box has 3 bool fields (essential, warm, liquid) → should cover all 8 combos."""
        info = all_models['Box']
        records = generate_coverage_set(info, 1, seed_config, BOX_FK_CACHE)
        combos = {(r.get('essential'), r.get('warm'), r.get('liquid')) for r in records}
        # Should have all 8 boolean combinations
        assert len(combos) == 8

    def test_fk_coverage_for_task(self, all_models, seed_config):
        """Every task category should appear at least once."""
        info = all_models['Task']
        records = generate_coverage_set(info, 1, seed_config, TASK_FK_CACHE)
        categories = {r['category'] for r in records}
        assert categories == set(TASK_FK_CACHE['task_categories.name'])

    def test_scale_multiplier(self, all_models, seed_config):
        info = all_models['Event']
        records_1x = generate_coverage_set(info, 1, seed_config, {})
        records_3x = generate_coverage_set(info, 3, seed_config, {})
        assert len(records_3x) >= len(records_1x) * 2  # ~3x, allow some tolerance

    def test_unique_fields_enforced(self, all_models, seed_config):
        """Box.number should be unique across all records."""
        info = all_models['Box']
        records = generate_coverage_set(info, 2, seed_config, BOX_FK_CACHE)
        numbers = [r['number'] for r in records if 'number' in r]
        assert len(numbers) == len(set(numbers))

    def test_book_tags_non_empty(self, all_models, seed_config):
        info = all_models['Book']
        records = generate_coverage_set(info, 1, seed_config, {})
        for r in records:
            assert r.get('tags'), f'Book record has empty tags: {r}'

    def test_chat_has_messages(self, all_models, seed_config):
        info = all_models['Chat']
        records = generate_coverage_set(info, 1, seed_config, {})
        for r in records:
            msgs = r.get('messages', [])
            assert len(msgs) >= 2, f'Chat should have ≥2 messages, got {len(msgs)}'

    def test_event_date_timezone_aware(self, all_models, seed_config):
        info = all_models['Event']
        records = generate_coverage_set(info, 1, seed_config, {})
        for r in records:
            d = r.get('date')
            if isinstance(d, datetime):
                assert d.tzinfo is not None, f'Event date should be timezone-aware: {d}'

    def test_nullable_coverage(self, all_models, seed_config):
        """At least one record should have a None value for nullable fields."""
        info = all_models['Event']
        records = generate_coverage_set(info, 1, seed_config, {})
        # 'notes' and 'url' are nullable
        notes_values = [r.get('notes') for r in records]
        assert None in notes_values, 'Should have at least one None notes'

    def test_string_length_never_exceeded(self, all_models, seed_config):
        """No string field should exceed its max_length."""
        for model_name, info in all_models.items():
            if info.is_lookup:
                continue
            fk_cache = TASK_FK_CACHE if model_name in ('Task', 'AutoTask') else {}
            if model_name == 'AutoTask':
                fk_cache = AUTOTASK_FK_CACHE
            elif model_name == 'Box':
                fk_cache = BOX_FK_CACHE
            elif model_name in ('Habit', 'HabitCompleted'):
                fk_cache = {'habits.categories.id': [1, 2, 3]}

            records = generate_coverage_set(info, 1, seed_config, fk_cache)
            for col in info.columns:
                if col.max_length:
                    for r in records:
                        val = r.get(col.name)
                        if isinstance(val, str):
                            assert len(val) <= col.max_length, f'{model_name}.{col.name}: "{val}" exceeds max_length {col.max_length}'
