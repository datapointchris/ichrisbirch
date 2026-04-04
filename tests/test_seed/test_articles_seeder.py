"""Tests for the articles seeder."""

from __future__ import annotations

import pytest

from scripts.seed.seeders import articles

pytestmark = [pytest.mark.seed, pytest.mark.integration]


class TestArticleSeeder:
    def test_creates_articles(self, db):
        articles.clear(db)
        result = articles.seed(db, scale=1)
        assert result.count > 0
