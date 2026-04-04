"""Tests for the projects seeder."""

from __future__ import annotations

import pytest

from ichrisbirch.models.project import ProjectItem
from ichrisbirch.models.project import ProjectItemMembership
from ichrisbirch.models.project import ProjectItemTask
from scripts.seed.seeders import projects

pytestmark = [pytest.mark.seed, pytest.mark.integration]


class TestProjectSeeder:
    def test_every_item_has_membership(self, db):
        projects.clear(db)
        projects.seed(db, scale=1)
        items = db.query(ProjectItem).all()
        for item in items:
            memberships = db.query(ProjectItemMembership).filter(ProjectItemMembership.item_id == item.id).count()
            assert memberships >= 1, f'Item {item.id} has no project membership'

    def test_every_task_has_parent_item(self, db):
        projects.clear(db)
        projects.seed(db, scale=1)
        tasks = db.query(ProjectItemTask).all()
        for task in tasks:
            item = db.query(ProjectItem).filter(ProjectItem.id == task.item_id).first()
            assert item is not None, f'Task {task.id} has no parent item'
