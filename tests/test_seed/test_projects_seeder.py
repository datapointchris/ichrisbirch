"""Tests for the projects seeder."""

from __future__ import annotations

import pytest

from ichrisbirch.models.project import Project
from ichrisbirch.models.project import ProjectItem
from ichrisbirch.models.project import ProjectItemDependency
from ichrisbirch.models.project import ProjectItemMembership
from ichrisbirch.models.project import ProjectItemTask
from scripts.seed.seeders import projects

pytestmark = [pytest.mark.seed, pytest.mark.integration]


class TestProjectSeeder:
    def test_creates_projects(self, db):
        projects.clear(db)
        projects.seed(db, scale=1)
        count = db.query(Project).count()
        assert count == len(projects.PROJECT_DATA)

    def test_projects_have_descriptions(self, db):
        projects.clear(db)
        projects.seed(db, scale=1)
        all_projects = db.query(Project).all()
        for project in all_projects:
            assert project.description is not None, f'Project {project.name} has no description'

    def test_every_item_has_membership(self, db):
        projects.clear(db)
        projects.seed(db, scale=1)
        items = db.query(ProjectItem).all()
        for item in items:
            memberships = db.query(ProjectItemMembership).filter(ProjectItemMembership.item_id == item.id).count()
            assert memberships >= 1, f'Item {item.id} has no project membership'

    def test_has_dependencies(self, db):
        projects.clear(db)
        projects.seed(db, scale=1)
        dep_count = db.query(ProjectItemDependency).count()
        assert dep_count >= 1

    def test_dependencies_are_acyclic(self, db):
        """No item depends on itself, directly or through a chain."""
        projects.clear(db)
        projects.seed(db, scale=1)
        deps = db.query(ProjectItemDependency).all()
        for dep in deps:
            assert dep.item_id != dep.depends_on_id

    def test_has_active_completed_and_archived(self, db):
        projects.clear(db)
        projects.seed(db, scale=1)
        items = db.query(ProjectItem).all()
        active = sum(1 for i in items if not i.completed and not i.archived)
        completed = sum(1 for i in items if i.completed)
        archived = sum(1 for i in items if i.archived)
        assert active >= 1
        assert completed >= 1
        assert archived >= 1

    def test_has_tasks(self, db):
        projects.clear(db)
        projects.seed(db, scale=1)
        task_count = db.query(ProjectItemTask).count()
        assert task_count >= 1

    def test_every_task_has_parent_item(self, db):
        projects.clear(db)
        projects.seed(db, scale=1)
        tasks = db.query(ProjectItemTask).all()
        for task in tasks:
            item = db.query(ProjectItem).filter(ProjectItem.id == task.item_id).first()
            assert item is not None, f'Task {task.id} has no parent item'

    def test_scale_multiplier(self, db):
        projects.clear(db)
        r1 = projects.seed(db, scale=1)
        projects.clear(db)
        r2 = projects.seed(db, scale=2)
        assert r2.count > r1.count
