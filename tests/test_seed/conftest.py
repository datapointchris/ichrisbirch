"""Seed test fixtures."""

from __future__ import annotations

import random

import pytest
from faker import Faker

from ichrisbirch.database.session import create_session
from tests.utils.database import test_settings


@pytest.fixture(autouse=True)
def seed_random():
    """Seed random generators for reproducibility."""
    Faker.seed(42)
    random.seed(42)


@pytest.fixture
def db():
    """Provide a database session for seed integration tests."""
    with create_session(test_settings) as session:
        yield session
