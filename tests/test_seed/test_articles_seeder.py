"""Tests for the articles seeder."""

from __future__ import annotations

import pytest

from ichrisbirch.models.article import Article
from scripts.seed.seeders import articles

pytestmark = [pytest.mark.seed, pytest.mark.integration]


class TestArticleSeeder:
    def test_creates_articles(self, db):
        articles.clear(db)
        result = articles.seed(db, scale=1)
        assert result.count == len(articles.ARTICLES)

    def test_has_current_article(self, db):
        articles.clear(db)
        articles.seed(db, scale=1)
        current = db.query(Article).filter(Article.is_current.is_(True)).count()
        assert current >= 1

    def test_has_archived_articles(self, db):
        articles.clear(db)
        articles.seed(db, scale=1)
        archived = db.query(Article).filter(Article.is_archived.is_(True)).count()
        assert archived >= 1

    def test_has_favorite_articles(self, db):
        articles.clear(db)
        articles.seed(db, scale=1)
        favorites = db.query(Article).filter(Article.is_favorite.is_(True)).count()
        assert favorites >= 1

    def test_scale_multiplier(self, db):
        articles.clear(db)
        r1 = articles.seed(db, scale=1)
        articles.clear(db)
        r2 = articles.seed(db, scale=2)
        assert r2.count > r1.count
