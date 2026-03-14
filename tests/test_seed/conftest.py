"""Seed-specific test fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest
from faker import Faker

from scripts.seed.config import SeedConfig
from scripts.seed.config import load_config
from scripts.seed.discovery import discover_models


@pytest.fixture
def seed_config() -> SeedConfig:
    """Load the default seed config."""
    config_path = Path(__file__).parent.parent.parent / 'scripts' / 'seed' / 'seed_config.toml'
    return load_config(config_path)


@pytest.fixture
def all_models():
    """Discover all models."""
    return discover_models()


@pytest.fixture(autouse=True)
def seed_faker():
    """Seed Faker for reproducible tests."""
    Faker.seed(42)
    import random

    random.seed(42)
