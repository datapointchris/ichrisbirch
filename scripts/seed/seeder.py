"""Orchestrator: discover → generate → insert."""

from __future__ import annotations

from pathlib import Path

import sqlalchemy
import structlog
from faker import Faker
from pydantic import ValidationError
from sqlalchemy.orm import Session

from ichrisbirch.config import Settings
from ichrisbirch.database.base import Base
from ichrisbirch.database.session import create_session
from scripts.seed.config import SeedConfig
from scripts.seed.config import load_config
from scripts.seed.discovery import ModelInfo
from scripts.seed.discovery import compute_insertion_order
from scripts.seed.discovery import discover_models
from scripts.seed.discovery import query_fk_values

logger = structlog.get_logger()


def _build_fk_cache(session: Session, models: dict[str, ModelInfo]) -> dict[str, list]:
    """Pre-query all FK lookup values across all models."""
    fk_cache: dict[str, list] = {}
    for model_info in models.values():
        for col in model_info.columns:
            if col.fk_target and col.fk_target not in fk_cache:
                values = query_fk_values(session, col)
                fk_cache[col.fk_target] = values
    return fk_cache


def _build_fk_cache_from_models(models: dict[str, ModelInfo]) -> dict[str, list]:
    """Build FK cache from module-level constants (no DB needed).

    Lookup tables define valid values as module-level constants:
    TASK_CATEGORIES, AUTOTASK_FREQUENCIES, BOX_SIZES.
    For non-lookup FKs (like box_id, chat_id), use placeholder IDs.
    """
    from ichrisbirch.models.autotask import AUTOTASK_FREQUENCIES
    from ichrisbirch.models.book import BOOK_OWNERSHIP_VALUES
    from ichrisbirch.models.book import BOOK_PROGRESS_VALUES
    from ichrisbirch.models.box import BOX_SIZES
    from ichrisbirch.models.task import TASK_CATEGORIES

    # Map FK targets to known values
    known_lookups = {
        'task_categories.name': TASK_CATEGORIES,
        'autotask_frequencies.name': AUTOTASK_FREQUENCIES,
        'book_ownership.name': BOOK_OWNERSHIP_VALUES,
        'book_progress.name': BOOK_PROGRESS_VALUES,
        'box_packing.box_sizes.name': BOX_SIZES,
    }

    fk_cache: dict[str, list] = {}
    for model_info in models.values():
        for col in model_info.columns:
            if col.fk_target and col.fk_target not in fk_cache:
                if col.fk_target in known_lookups:
                    fk_cache[col.fk_target] = known_lookups[col.fk_target].copy()
                else:
                    # For non-lookup FKs, use placeholder IDs for dry-run
                    fk_cache[col.fk_target] = list(range(1, 6))

    return fk_cache


def _validate_record(record: dict, model_info: ModelInfo, model_name: str) -> bool:
    """Validate a record against its Create schema."""
    if not model_info.create_schema:
        return True
    try:
        model_info.create_schema(**record)
        return True
    except ValidationError as e:
        logger.warning('validation_failed', model=model_name, errors=str(e), record=record)
        return False


def _insert_records(
    session: Session,
    model_info: ModelInfo,
    records: list[dict],
    model_name: str,
    created_ids: dict[str, list[int]],
):
    """Insert records into the database and track created IDs."""
    # Identify relationship fields that need special handling
    # (e.g., Chat.messages expects ChatMessage objects, not dicts)
    rel_fields = {r.name for r in model_info.relationships}

    instances = []
    deferred_children: list[tuple[object, str, list[dict]]] = []

    for record in records:
        # Extract relationship data before constructing the model instance
        child_data = {}
        for field_name in list(record.keys()):
            if field_name in rel_fields:
                child_data[field_name] = record.pop(field_name)

        obj = model_info.model_class(**record)
        instances.append(obj)

        for field_name, children in child_data.items():
            if isinstance(children, list):
                deferred_children.append((obj, field_name, children))

    session.add_all(instances)
    session.flush()

    # Now create child objects with proper parent IDs
    for parent, rel_name, children in deferred_children:
        rel_info = next(r for r in model_info.relationships if r.name == rel_name)
        # Find the child model class
        child_model = None
        for mapper in Base.registry.mappers:
            if mapper.class_.__name__ == rel_info.target_model_name:
                child_model = mapper.class_
                break
        if child_model and children:
            # Determine the FK column name on the child that points to parent
            parent_id = parent.id
            child_fk_col = None
            child_insp = sqlalchemy.inspect(child_model)
            for col in child_insp.columns:
                if col.foreign_keys:
                    for fk in col.foreign_keys:
                        parent_table = model_info.table_name
                        if model_info.schema_name:
                            parent_table = f'{model_info.schema_name}.{parent_table}'
                        if parent_table in str(fk.target_fullname):
                            child_fk_col = col.name
                            break

            for child_dict in children:
                if child_fk_col:
                    child_dict[child_fk_col] = parent_id
                child_obj = child_model(**child_dict)
                session.add(child_obj)

    session.flush()

    created_ids[model_name] = [obj.id for obj in instances if hasattr(obj, 'id')]
    logger.info('inserted', model=model_name, count=len(instances))


def _update_fk_cache_with_created_ids(
    fk_cache: dict[str, list],
    created_ids: dict[str, list[int]],
    models: dict[str, ModelInfo],
):
    """Update FK cache with IDs from freshly inserted records."""
    for model_name, ids in created_ids.items():
        if model_name not in models:
            continue
        info = models[model_name]
        pk_col = next((c for c in info.columns if c.is_primary_key), None)
        if pk_col:
            if info.schema_name:
                fk_key = f'{info.schema_name}.{info.table_name}.{pk_col.name}'
            else:
                fk_key = f'{info.table_name}.{pk_col.name}'
            fk_cache[fk_key] = ids


def _seed_project_ecosystem(
    session: Session | None,
    created_ids: dict[str, list[int]],
    config: SeedConfig,
    scale: int,
    dry_run: bool = False,
) -> dict[str, int]:
    """Seed ProjectItems with memberships and dependencies.

    Handled separately from the generic flow because:
    - Every ProjectItem must have ≥1 ProjectItemMembership (M-N join)
    - ProjectItemCreate schema requires project_ids (not a DB column)
    - Dependencies must be acyclic and coordinated with memberships
    - We want realistic coverage of completed/archived/multi-project states
    """

    project_ids = created_ids.get('Project', [])
    if not project_ids:
        logger.warning('skip_project_ecosystem', reason='no projects seeded')
        return {}

    title_pool = config.get_pool('ProjectItem', 'title') or [f'Project task {i}' for i in range(1, 16)]
    notes_pool = config.get_pool('ProjectItem', 'notes') or ['Check requirements first', 'Low priority', 'Discuss in next meeting']

    # State coverage cycle: (completed, archived)
    # Weighted toward active items for realistic distribution
    state_cycle = [
        (False, False),  # active
        (False, False),  # active
        (False, False),  # active
        (True, False),  # completed
        (False, True),  # archived
        (True, True),  # completed + archived
    ]

    target_count = len(title_pool) * scale
    records = []
    for i in range(target_count):
        title = title_pool[i % len(title_pool)]
        if scale > 1 and i >= len(title_pool):
            title = f'{title} #{i // len(title_pool) + 1}'
        completed, archived = state_cycle[i % len(state_cycle)]
        notes = notes_pool[i % len(notes_pool)] if i % 3 != 0 else None
        records.append(dict(title=title, notes=notes, completed=completed, archived=archived))

    summary = {'ProjectItem': len(records)}

    if dry_run:
        memberships = target_count + target_count // 4
        deps = min(2, len(project_ids)) * scale
        logger.info('dry_run_project_ecosystem', items=len(records), memberships=memberships, dependencies=deps)
        return summary

    from ichrisbirch.models.project import ProjectItem
    from ichrisbirch.models.project import ProjectItemDependency
    from ichrisbirch.models.project import ProjectItemMembership

    # Clear existing project items and relationships for clean reruns
    session.execute(sqlalchemy.text('DELETE FROM project_item_dependencies'))
    session.execute(sqlalchemy.text('DELETE FROM project_item_memberships'))
    session.execute(sqlalchemy.text('DELETE FROM project_items'))
    session.flush()

    # Insert items
    items = []
    for record in records:
        item = ProjectItem(**record)
        session.add(item)
        items.append(item)
    session.flush()

    # Memberships: distribute items round-robin, some with dual membership
    membership_count = 0
    for i, item in enumerate(items):
        primary = project_ids[i % len(project_ids)]
        session.add(ProjectItemMembership(item_id=item.id, project_id=primary, position=i // len(project_ids)))
        membership_count += 1

        # ~25% of items belong to a second project
        if i % 4 == 0 and len(project_ids) > 1:
            secondary = project_ids[(i + 1) % len(project_ids)]
            session.add(ProjectItemMembership(item_id=item.id, project_id=secondary, position=99))
            membership_count += 1
    session.flush()

    # Dependencies: short chains within each project (acyclic by construction)
    dep_count = 0
    items_by_project: dict[int, list[int]] = {}
    for i, item in enumerate(items):
        proj = project_ids[i % len(project_ids)]
        items_by_project.setdefault(proj, []).append(item.id)

    for item_ids_in_proj in items_by_project.values():
        # Chain first 2-3 active items: item[1] depends on item[0], etc.
        chain_len = min(3, len(item_ids_in_proj))
        for j in range(1, chain_len):
            session.add(ProjectItemDependency(item_id=item_ids_in_proj[j], depends_on_id=item_ids_in_proj[j - 1]))
            dep_count += 1
    session.flush()

    created_ids['ProjectItem'] = [item.id for item in items]
    logger.info('seeded_project_ecosystem', items=len(items), memberships=membership_count, dependencies=dep_count)
    return summary


def run_seed(
    settings: Settings,
    scale: int = 1,
    config_path: Path | None = None,
    dry_run: bool = False,
    only: list[str] | None = None,
    faker_seed: int = 42,
    verbose: bool = False,
):
    """Main entry point: discover models, generate data, insert into DB."""
    Faker.seed(faker_seed)
    import random

    random.seed(faker_seed)

    # Load config
    if config_path is None:
        config_path = Path(__file__).parent / 'seed_config.toml'
    config = load_config(config_path)
    config.scale = scale

    logger.info('seed_starting', scale=scale, dry_run=dry_run, faker_seed=faker_seed)

    # Discover models
    all_models = discover_models()
    logger.info('models_discovered', count=len(all_models), models=sorted(all_models.keys()))

    # Filter to seedable (non-lookup, non-system)
    seedable = {name: info for name, info in all_models.items() if not info.is_lookup and name not in config.skip_models}

    if only:
        seedable = {name: info for name, info in seedable.items() if name in only}

    # Compute insertion order
    order = compute_insertion_order(seedable)
    logger.info('insertion_order', order=order)

    from scripts.seed.generator import generate_coverage_set

    if dry_run:
        # Build FK cache from model definitions (no DB needed)
        fk_cache = _build_fk_cache_from_models(all_models)

        if verbose:
            for key, values in fk_cache.items():
                logger.info('fk_cache', target=key, count=len(values), sample=values[:5])

        summary: dict[str, int] = {}
        for model_name in order:
            info = seedable[model_name]
            records = generate_coverage_set(info, scale, config, fk_cache)

            valid_records = []
            for record in records:
                if _validate_record(record, info, model_name):
                    valid_records.append(record)
                elif verbose:
                    logger.warning('skipping_invalid_record', model=model_name, record=record)

            summary[model_name] = len(valid_records)
            logger.info('dry_run', model=model_name, count=len(valid_records))
            if verbose and valid_records:
                logger.info('sample_record', model=model_name, record=valid_records[0])

        # Project ecosystem (items + memberships + deps)
        if only is None or 'ProjectItem' in only:
            dry_ids = {'Project': list(range(1, summary.get('Project', 0) + 1))}
            eco_summary = _seed_project_ecosystem(None, dry_ids, config, scale, dry_run=True)
            summary.update(eco_summary)

        total = sum(summary.values())
        logger.info('seed_summary', total=total, per_model=summary)
        return

    # Live seed: connect to DB
    with create_session(settings) as session:
        fk_cache = _build_fk_cache(session, all_models)

        if verbose:
            for key, values in fk_cache.items():
                logger.info('fk_cache', target=key, count=len(values), sample=values[:5])

        # Verify static lookup tables have data (only check FKs that point
        # to lookup tables NOT being seeded — parent tables like HabitCategory
        # will be populated by the seeder itself)
        seedable_tables = set()
        for info in seedable.values():
            key_prefix = f'{info.schema_name}.{info.table_name}' if info.schema_name else info.table_name
            seedable_tables.add(key_prefix)

        for model_name in order:
            info = seedable[model_name]
            for col in info.columns:
                if col.fk_target and col.fk_target in fk_cache and not fk_cache[col.fk_target]:
                    # Check if the FK target table is being seeded
                    fk_table = col.fk_target.rsplit('.', 1)[0]
                    if fk_table in seedable_tables:
                        continue
                    logger.error(
                        'empty_lookup_table',
                        model=model_name,
                        column=col.name,
                        fk_target=col.fk_target,
                    )
                    raise RuntimeError(f'Lookup table for {col.fk_target} is empty. Run database initialization first.')

        # Truncate seeded tables in reverse order (children first) for clean reruns
        for model_name in reversed(order):
            info = seedable[model_name]
            table = info.table_name
            if info.schema_name:
                table = f'{info.schema_name}.{table}'
            session.execute(sqlalchemy.text(f'DELETE FROM {table}'))
            logger.info('cleared', table=table)
        session.flush()

        created_ids: dict[str, list[int]] = {}
        summary = {}

        for model_name in order:
            info = seedable[model_name]
            records = generate_coverage_set(info, scale, config, fk_cache)

            valid_records = []
            for record in records:
                if _validate_record(record, info, model_name):
                    valid_records.append(record)
                elif verbose:
                    logger.warning('skipping_invalid_record', model=model_name, record=record)

            summary[model_name] = len(valid_records)

            if valid_records:
                _insert_records(session, info, valid_records, model_name, created_ids)
                _update_fk_cache_with_created_ids(fk_cache, created_ids, all_models)

        # Project ecosystem: items + memberships + dependencies
        if only is None or 'ProjectItem' in only:
            eco_summary = _seed_project_ecosystem(session, created_ids, config, scale)
            summary.update(eco_summary)

        session.commit()
        logger.info('seed_committed')

        total = sum(summary.values())
        logger.info('seed_summary', total=total, per_model=summary)
