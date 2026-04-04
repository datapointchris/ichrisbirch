"""Tests for the boxes seeder."""

from __future__ import annotations

import pytest

from ichrisbirch.models.box import Box
from ichrisbirch.models.boxitem import BoxItem
from scripts.seed.seeders import boxes

pytestmark = [pytest.mark.seed, pytest.mark.integration]


class TestBoxSeeder:
    def test_creates_boxes_for_all_sizes(self, db):
        boxes.clear(db)
        boxes.seed(db, scale=1)
        sizes = {b.size for b in db.query(Box).all()}
        expected = {name for _, name in boxes.BOX_NAMES}
        assert sizes == expected

    def test_creates_items_distributed_across_boxes(self, db):
        boxes.clear(db)
        boxes.seed(db, scale=1)
        item_count = db.query(BoxItem).count()
        assert item_count == len(boxes.ITEMS)
        all_items = db.query(BoxItem).all()
        boxed_ids = {i.box_id for i in all_items if i.box_id is not None}
        unboxed = [i for i in all_items if i.box_id is None]
        all_box_ids = {b.id for b in db.query(Box).all()}
        assert boxed_ids.issubset(all_box_ids)
        assert len(unboxed) >= 1, 'Should have at least one unboxed item'

    def test_boxes_have_unique_numbers(self, db):
        boxes.clear(db)
        boxes.seed(db, scale=1)
        all_boxes = db.query(Box).all()
        numbers = [b.number for b in all_boxes]
        assert len(numbers) == len(set(numbers))

    def test_scale_multiplier(self, db):
        boxes.clear(db)
        r1 = boxes.seed(db, scale=1)
        boxes.clear(db)
        r2 = boxes.seed(db, scale=2)
        assert r2.count > r1.count
