"""Data generation engine: type→Faker mapping + combinatorial coverage."""

from __future__ import annotations

import itertools
import random
from datetime import UTC
from datetime import date
from datetime import datetime

from faker import Faker

from scripts.seed.config import SeedConfig
from scripts.seed.discovery import ColumnInfo
from scripts.seed.discovery import ModelInfo
from scripts.seed.discovery import get_seedable_columns

fake = Faker()

# Field name substrings → Faker provider
NAME_HEURISTICS: dict[str, callable] = {
    'email': fake.email,
    'url': fake.url,
    'isbn': fake.isbn13,
    'author': fake.name,
    'venue': lambda: f'{fake.company()} {random.choice(["Hall", "Arena", "Center", "Lounge", "Theater"])}',
    'color': fake.hex_color,
    'title': lambda: fake.sentence(nb_words=4).rstrip('.'),
    'content': lambda: fake.paragraph(nb_sentences=3),
    'summary': lambda: fake.paragraph(nb_sentences=2),
    'notes': fake.sentence,
    'item': fake.catch_phrase,
}

# Python type → Faker generator
TYPE_GENERATORS: dict[type, callable] = {
    str: lambda col: fake.text(max_nb_chars=min(col.max_length or 100, 100)),
    int: lambda _col: fake.random_int(min=1, max=100),
    float: lambda _col: round(fake.pyfloat(min_value=0.01, max_value=500.0, right_digits=2), 2),
    bool: lambda _col: fake.boolean(),
    datetime: lambda _col: fake.date_time_between('-1y', 'now', tzinfo=UTC),
    date: lambda _col: fake.date_between('-1y', '+1y'),
    list: lambda _col: [fake.word() for _ in range(fake.random_int(1, 5))],
}


def generate_value(col: ColumnInfo, config: SeedConfig, model_name: str, fk_cache: dict[str, list], counters: dict[str, int]) -> object:
    """Generate a single value for a column, following the resolution order."""
    # 1. Config pool override
    pool = config.get_pool(model_name, col.name)
    if pool:
        return random.choice(pool)

    # 2. FK values — cycle through valid values
    if col.fk_target and col.fk_target in fk_cache:
        values = fk_cache[col.fk_target]
        if values:
            key = f'{model_name}.{col.name}'
            idx = counters.get(key, 0)
            counters[key] = idx + 1
            return values[idx % len(values)]

    # 3. Name heuristic
    for hint, generator in NAME_HEURISTICS.items():
        if hint in col.name.lower():
            value = generator()
            if col.max_length and isinstance(value, str):
                value = value[: col.max_length]
            return value

    # 4. Special: name field gets catch_phrase
    if col.name == 'name':
        value = fake.catch_phrase()
        if col.max_length:
            value = value[: col.max_length]
        return value

    # 5. Type fallback
    gen = TYPE_GENERATORS.get(col.python_type)
    if gen:
        value = gen(col)
        if col.max_length and isinstance(value, str):
            value = value[: col.max_length]
        return value

    return fake.word()


def _identify_axes(model_info: ModelInfo, fk_cache: dict[str, list]) -> tuple[dict[str, list], list[str], list[str]]:
    """Identify FK axes, boolean axes, and nullable fields for coverage."""
    cols = get_seedable_columns(model_info)
    fk_axes: dict[str, list] = {}
    bool_axes: list[str] = []
    nullable_fields: list[str] = []

    # Determine which fields are optional in the Create schema
    schema_optional: set[str] = set()
    if model_info.create_schema:
        for fname, finfo in model_info.create_schema.model_fields.items():
            if not finfo.is_required():
                schema_optional.add(fname)

    for col in cols:
        if col.fk_target and col.fk_target in fk_cache and fk_cache[col.fk_target]:
            fk_axes[col.name] = fk_cache[col.fk_target]
        elif col.python_type is bool and not col.has_default:
            bool_axes.append(col.name)
        # Only include nullable fields that are also optional in the schema
        if col.nullable and not col.is_primary_key and not col.fk_target and (not model_info.create_schema or col.name in schema_optional):
            nullable_fields.append(col.name)

    return fk_axes, bool_axes, nullable_fields


def _generate_base_record(
    model_info: ModelInfo,
    config: SeedConfig,
    fk_cache: dict[str, list],
    counters: dict[str, int],
) -> dict:
    """Generate a single record with all fields populated."""
    record = {}
    model_name = model_info.model_class.__name__

    # Use Create schema fields if available to know what fields to generate
    if model_info.create_schema:
        schema_fields = model_info.create_schema.model_fields
        cols_by_name = {c.name: c for c in model_info.columns}

        for field_name, _field_info in schema_fields.items():
            col = cols_by_name.get(field_name)
            if col:
                record[field_name] = generate_value(col, config, model_name, fk_cache, counters)
            else:
                # Schema field not in columns (e.g., 'messages' in ChatCreate)
                # Handle via special cases below
                pass
    else:
        for col in get_seedable_columns(model_info):
            if col.has_default and col.nullable:
                continue
            record[col.name] = generate_value(col, config, model_name, fk_cache, counters)

    return record


def _apply_book_consistency(record: dict, config: SeedConfig) -> None:
    """Enforce realistic field combinations for Book records.

    Ownership controls which fields are allowed:
      owned/donated — no sell_date/sell_price, no reject_reason
      sold          — must have sell_date, no reject_reason
      to_purchase   — no purchase/sell/read dates, progress must be unread
      rejected      — no purchase/sell/read dates, must have reject_reason, progress must be unread

    Progress controls read date and rating consistency:
      unread    — no read dates, no rating
      reading   — must have read_start_date, no read_finish_date, no rating
      read      — must have both read dates (start < finish), rating allowed
      abandoned — must have read_start_date, no read_finish_date, no rating
    """
    ownership = record.get('ownership', 'owned')
    progress = record.get('progress', 'unread')

    # --- Ownership constraints ---
    if ownership in ('to_purchase', 'rejected'):
        # Never owned: no purchase, sell, or reading activity
        for field in ('purchase_date', 'purchase_price', 'sell_date', 'sell_price', 'read_start_date', 'read_finish_date', 'rating'):
            record[field] = None
        record['progress'] = 'unread'
        progress = 'unread'

        if ownership == 'rejected':
            if not record.get('reject_reason'):
                pool = config.get_pool('Book', 'reject_reason')
                record['reject_reason'] = random.choice(pool) if pool else 'Superseded by a better alternative'
        else:
            record['reject_reason'] = None
        return

    # owned, sold, donated — no reject_reason
    record['reject_reason'] = None

    if ownership == 'sold':
        # Must have sell_date
        if not record.get('sell_date'):
            record['sell_date'] = fake.date_time_between('-1y', 'now', tzinfo=UTC)
    else:
        # owned and donated: no sell info
        record['sell_date'] = None
        record['sell_price'] = None

    # --- Progress constraints ---
    if progress == 'unread':
        record['read_start_date'] = None
        record['read_finish_date'] = None
        record['rating'] = None
    elif progress == 'reading':
        if not record.get('read_start_date'):
            record['read_start_date'] = fake.date_time_between('-6m', 'now', tzinfo=UTC)
        record['read_finish_date'] = None
        record['rating'] = None
    elif progress == 'read':
        start = record.get('read_start_date') or fake.date_time_between('-2y', '-2m', tzinfo=UTC)
        finish = record.get('read_finish_date') or fake.date_time_between('-2m', 'now', tzinfo=UTC)
        if start > finish:
            start, finish = finish, start
        record['read_start_date'] = start
        record['read_finish_date'] = finish
        # Rating 1-10 for finished books
        record['rating'] = record.get('rating') or random.randint(1, 10)
        if record['rating'] > 10:
            record['rating'] = random.randint(1, 10)
    elif progress == 'abandoned':
        if not record.get('read_start_date'):
            record['read_start_date'] = fake.date_time_between('-1y', 'now', tzinfo=UTC)
        record['read_finish_date'] = None
        record['rating'] = None

    # Pair purchase fields: price without date doesn't make sense
    if record.get('purchase_price') and not record.get('purchase_date'):
        record['purchase_date'] = fake.date_time_between('-3y', '-6m', tzinfo=UTC)
    # Similarly for sell
    if record.get('sell_price') and not record.get('sell_date'):
        record['sell_price'] = None


def _apply_special_rules(record: dict, model_name: str, config: SeedConfig, fk_cache: dict[str, list], counters: dict[str, int]) -> dict:
    """Apply model-specific rules that can't be handled generically."""
    if model_name == 'Book':
        # tags must be non-empty list[str] (schema validator rejects [])
        tags = record.get('tags')
        if not tags or not isinstance(tags, list) or (tags and isinstance(tags[0], list)):
            pool = config.get_pool('Book', 'tags')
            if pool:
                record['tags'] = random.choice(pool)
            else:
                record['tags'] = [fake.word() for _ in range(random.randint(1, 4))]

        _apply_book_consistency(record, config)

    elif model_name == 'Duration':
        # end_date must be after start_date when both exist
        start = record.get('start_date')
        end = record.get('end_date')
        if start and end and end < start:
            record['start_date'], record['end_date'] = end, start

    elif model_name == 'Article':
        # tags should be a list of strings
        tags = record.get('tags')
        if not tags or not isinstance(tags, list) or (tags and isinstance(tags[0], list)):
            pool = config.get_pool('Article', 'tags')
            if pool:
                record['tags'] = random.choice(pool)
            else:
                record['tags'] = [fake.word() for _ in range(random.randint(1, 4))]
        # save_date is required
        if 'save_date' not in record:
            record['save_date'] = fake.date_time_between('-1y', 'now', tzinfo=UTC)

    elif model_name == 'Chat':
        # messages list is required
        if 'messages' not in record or not record.get('messages'):
            num_msgs = random.randint(2, 5)
            roles = itertools.cycle(['user', 'assistant'])
            record['messages'] = [{'role': next(roles), 'content': fake.paragraph(nb_sentences=2)} for _ in range(num_msgs)]

    elif model_name == 'Event':
        # Generic datetime generator produces past-only dates; override so most events are upcoming
        if 'date' in record:
            record['date'] = fake.date_time_between('-2m', '+1y', tzinfo=UTC)

    elif model_name == 'HabitCompleted':
        # complete_date must be timezone-aware
        if 'complete_date' in record and isinstance(record['complete_date'], datetime) and record['complete_date'].tzinfo is None:
            record['complete_date'] = record['complete_date'].replace(tzinfo=UTC)

    return record


def generate_coverage_set(
    model_info: ModelInfo,
    scale: int,
    config: SeedConfig,
    fk_cache: dict[str, list],
) -> list[dict]:
    """Generate a coverage set of records for a model.

    Ensures every FK value, boolean combination, and nullable variant is covered,
    then fills to target count with random records.
    """
    model_name = model_info.model_class.__name__
    counters: dict[str, int] = {}
    records: list[dict] = []

    fk_axes, bool_axes, nullable_fields = _identify_axes(model_info, fk_cache)

    # Boolean coverage: all combinations
    if bool_axes:
        bool_combos = list(itertools.product([True, False], repeat=len(bool_axes)))
    else:
        bool_combos = [()]

    # FK coverage: one record per FK value (for the largest FK axis)
    max_fk_count = max((len(v) for v in fk_axes.values()), default=0)

    coverage_count = max(len(bool_combos), max_fk_count, 3)
    target = coverage_count * scale

    # Generate coverage records: merge bool combos with FK cycling
    fk_iterators = {name: itertools.cycle(values) for name, values in fk_axes.items()}

    for i in range(target):
        record = _generate_base_record(model_info, config, fk_cache, counters)

        # Apply bool combo (cycle through combos)
        if bool_axes:
            combo = bool_combos[i % len(bool_combos)]
            for axis_name, value in zip(bool_axes, combo, strict=False):
                record[axis_name] = value

        # Apply FK cycling
        for fk_name, fk_iter in fk_iterators.items():
            record[fk_name] = next(fk_iter)

        # Nullable coverage: first few records get None for nullable fields
        if nullable_fields and i < len(nullable_fields):
            null_field = nullable_fields[i % len(nullable_fields)]
            if null_field in record:
                record[null_field] = None

        record = _apply_special_rules(record, model_name, config, fk_cache, counters)
        records.append(record)

    # Enforce uniqueness for fields that need it
    _enforce_uniqueness(records, model_info, model_name)

    return records


def _enforce_uniqueness(records: list[dict], model_info: ModelInfo, model_name: str):
    """Ensure unique-constrained fields have unique values across records."""
    unique_cols = [c for c in model_info.columns if c.is_unique and not c.is_primary_key]

    for col in unique_cols:
        if col.name not in records[0]:
            continue
        seen: set = set()
        for i, record in enumerate(records):
            val = record.get(col.name)
            if val is None:
                continue

            if col.python_type is int:
                record[col.name] = i + 1
                continue

            original = val
            counter = 1
            while val in seen:
                suffix = f' #{counter}'
                if col.max_length:
                    val = original[: col.max_length - len(suffix)] + suffix
                else:
                    val = f'{original}{suffix}'
                counter += 1
            seen.add(val)
            record[col.name] = val
