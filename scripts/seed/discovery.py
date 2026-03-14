"""Model and schema introspection for auto-discovering seedable entities."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from graphlib import TopologicalSorter

import sqlalchemy
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Session

import ichrisbirch.models  # noqa: F401 — populates Base.registry
import ichrisbirch.schemas as schemas_module
from ichrisbirch.database.base import Base

SYSTEM_MODELS = frozenset(
    {
        'User',
        'JWTRefreshToken',
        'PersonalAPIKey',
        'BackupHistory',
        'BackupRestore',
    }
)

LOOKUP_MODELS = frozenset(
    {
        'TaskCategory',
        'AutoTaskFrequency',
        'BoxSize',
    }
)

SKIP_MODELS = frozenset(
    {
        'Apartment',
        'Feature',
        'PortfolioProject',
        'JournalEntry',
        'ArticleFailedImport',
    }
)


@dataclass
class ColumnInfo:
    name: str
    python_type: type
    sql_type_name: str
    max_length: int | None
    nullable: bool
    is_primary_key: bool
    is_unique: bool
    has_default: bool
    fk_target: str | None
    is_array: bool
    is_jsonb: bool


@dataclass
class RelationshipInfo:
    name: str
    target_model_name: str
    direction: str
    cascade: str | None


@dataclass
class ModelInfo:
    model_class: type
    create_schema: type | None
    table_name: str
    schema_name: str | None
    columns: list[ColumnInfo] = field(default_factory=list)
    relationships: list[RelationshipInfo] = field(default_factory=list)
    is_lookup: bool = False
    is_system: bool = False
    depends_on: set[str] = field(default_factory=set)


def _get_python_type(col) -> type:
    """Map a SQLAlchemy column type to a Python type."""
    from datetime import date
    from datetime import datetime

    type_name = type(col.type).__name__

    if isinstance(col.type, ARRAY):
        return list

    type_map = {
        'Integer': int,
        'BigInteger': int,
        'SmallInteger': int,
        'Float': float,
        'Numeric': float,
        'String': str,
        'Text': str,
        'Boolean': bool,
        'DateTime': datetime,
        'Date': date,
        'JSON': dict,
        'JSONB': dict,
    }
    # Handle MutableJSONB and similar wrappers
    if hasattr(col.type, 'impl'):
        impl_name = type(col.type.impl).__name__
        if impl_name in type_map:
            return type_map[impl_name]
    return type_map.get(type_name, str)


def _get_max_length(col) -> int | None:
    """Extract max length from String(N) columns."""
    col_type = col.type
    if isinstance(col_type, ARRAY):
        return None
    if hasattr(col_type, 'length') and col_type.length:
        return col_type.length
    return None


def _is_jsonb(col) -> bool:
    type_name = type(col.type).__name__
    if type_name == 'JSONB':
        return True
    if hasattr(col.type, 'impl'):
        return type(col.type.impl).__name__ == 'JSONB'
    return False


def _inspect_column(col) -> ColumnInfo:
    """Build ColumnInfo from a SQLAlchemy column."""
    fk_target = None
    if col.foreign_keys:
        fk = next(iter(col.foreign_keys))
        fk_target = str(fk.target_fullname)

    has_default = col.default is not None or col.server_default is not None

    return ColumnInfo(
        name=col.name,
        python_type=_get_python_type(col),
        sql_type_name=type(col.type).__name__,
        max_length=_get_max_length(col),
        nullable=col.nullable if col.nullable is not None else True,
        is_primary_key=col.primary_key,
        is_unique=col.unique or False,
        has_default=has_default,
        fk_target=fk_target,
        is_array=isinstance(col.type, ARRAY),
        is_jsonb=_is_jsonb(col),
    )


def _find_model_for_table(table_name: str, schema: str | None) -> type | None:
    """Find the model class that maps to a given table name and schema."""
    for mapper in Base.registry.mappers:
        cls = mapper.class_
        table = mapper.local_table
        if table is None:
            continue
        t_schema = getattr(table, 'schema', None)
        t_name = table.name
        if t_name == table_name and t_schema == schema:
            return cls
    return None


def discover_models() -> dict[str, ModelInfo]:
    """Walk Base.registry.mappers and build ModelInfo for each model."""
    models: dict[str, ModelInfo] = {}

    for mapper in Base.registry.mappers:
        cls = mapper.class_
        class_name = cls.__name__

        if class_name in SYSTEM_MODELS or class_name in SKIP_MODELS:
            continue

        table = mapper.local_table
        if table is None:
            continue

        table_name = table.name
        schema_name = getattr(table, 'schema', None)

        # Find matching Create schema
        create_schema = getattr(schemas_module, f'{class_name}Create', None)

        info = ModelInfo(
            model_class=cls,
            create_schema=create_schema,
            table_name=table_name,
            schema_name=schema_name,
            is_lookup=class_name in LOOKUP_MODELS,
            is_system=class_name in SYSTEM_MODELS,
        )

        # Inspect columns
        insp = sa_inspect(cls)
        for col in insp.columns:
            col_info = _inspect_column(col)
            info.columns.append(col_info)

            # Track FK dependencies
            if col_info.fk_target:
                fk_table = col_info.fk_target.rsplit('.', 1)[0]
                fk_schema = None
                if '.' in fk_table:
                    fk_schema, fk_table = fk_table.split('.', 1)
                dep_cls = _find_model_for_table(fk_table, fk_schema)
                if dep_cls and dep_cls.__name__ != class_name:
                    dep_name = dep_cls.__name__
                    if dep_name not in SYSTEM_MODELS and dep_name not in SKIP_MODELS:
                        info.depends_on.add(dep_name)

        # Inspect relationships
        for rel in insp.relationships:
            cascade = str(rel.cascade) if rel.cascade else None
            info.relationships.append(
                RelationshipInfo(
                    name=rel.key,
                    target_model_name=rel.mapper.class_.__name__,
                    direction=rel.direction.name,
                    cascade=cascade,
                )
            )

        models[class_name] = info

    return models


def compute_insertion_order(models: dict[str, ModelInfo]) -> list[str]:
    """Topological sort of models by FK dependencies."""
    graph: dict[str, set[str]] = {}
    for name, info in models.items():
        deps = {d for d in info.depends_on if d in models}
        graph[name] = deps

    sorter = TopologicalSorter(graph)
    return list(sorter.static_order())


def query_fk_values(session: Session, column_info: ColumnInfo) -> list:
    """Query the lookup/parent table for valid FK values."""
    if not column_info.fk_target:
        return []

    parts = column_info.fk_target.split('.')
    if len(parts) == 3:
        schema, table, col = parts
        full_table = f'{schema}.{table}'
    elif len(parts) == 2:
        full_table, col = parts
    else:
        return []

    result = session.execute(sqlalchemy.text(f'SELECT {col} FROM {full_table}'))
    return [row[0] for row in result.fetchall()]


def get_seedable_columns(model_info: ModelInfo) -> list[ColumnInfo]:
    """Get columns that should be populated during seeding (non-PK, non-default-only)."""
    return [col for col in model_info.columns if not col.is_primary_key]
