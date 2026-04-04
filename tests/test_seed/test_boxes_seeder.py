"""Tests for the boxes seeder."""

from __future__ import annotations

import pytest

from ichrisbirch.models.box import Box
from scripts.seed.seeders import boxes

pytestmark = [pytest.mark.seed, pytest.mark.integration]


class TestBoxSeeder:
    def test_creates_boxes_for_all_sizes(self, db):
        boxes.clear(db)
        boxes.seed(db, scale=1)
        sizes = {b.size for b in db.query(Box).all()}
        expected = {name for _, name in boxes.BOX_NAMES}
        assert sizes == expected

    def test_boxes_have_unique_numbers(self, db):
        boxes.clear(db)
        boxes.seed(db, scale=1)
        all_boxes = db.query(Box).all()
        numbers = [b.number for b in all_boxes]
        assert len(numbers) == len(set(numbers))
