"""Tests for the shopping seeder."""

from __future__ import annotations

import pytest

from ichrisbirch.models.shopping import ShoppingItem
from ichrisbirch.models.shopping import ShoppingPurchase
from scripts.seed.seeders import shopping

pytestmark = [pytest.mark.seed, pytest.mark.integration]


class TestShoppingSeeder:
    def test_seeds_a_list_with_unsorted_items_and_a_history(self, db):
        shopping.clear(db)
        shopping.seed(db, scale=1)
        items = db.query(ShoppingItem).all()
        assert any(item.is_needed and item.section_id is None for item in items)
        assert any(not item.is_needed for item in items)
        assert db.query(ShoppingPurchase).count() > 0

    @pytest.mark.parametrize('scale', [1, 3])
    def test_names_stay_unique_at_every_scale(self, db, scale):
        shopping.clear(db)
        shopping.seed(db, scale=scale)
        names = [item.name.lower() for item in db.query(ShoppingItem).all()]
        assert len(names) == len(set(names))
