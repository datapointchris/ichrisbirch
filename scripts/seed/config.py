"""TOML config loading for seed overrides."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path


@dataclass
class SeedConfig:
    scale: int = 1
    faker_seed: int = 42
    skip_models: list[str] = field(default_factory=list)
    overrides: dict[str, dict[str, dict]] = field(default_factory=dict)

    def get_pool(self, model_name: str, field_name: str) -> list | None:
        """Get a curated value pool for a specific model field, or None."""
        model_overrides = self.overrides.get(model_name, {})
        field_override = model_overrides.get(field_name, {})
        pool = field_override.get('pool')
        if pool:
            return list(pool)
        return None


def load_config(config_path: Path) -> SeedConfig:
    """Load seed config from TOML file."""
    if not config_path.exists():
        return SeedConfig()

    with config_path.open('rb') as f:
        raw = tomllib.load(f)

    seed_section = raw.get('seed', {})
    overrides_section = raw.get('overrides', {})

    return SeedConfig(
        scale=seed_section.get('scale', 1),
        faker_seed=seed_section.get('faker_seed', 42),
        skip_models=seed_section.get('skip_models', []),
        overrides=overrides_section,
    )
