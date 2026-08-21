"""Tests for the projects seeder."""

from __future__ import annotations

import pytest

from ichrisbirch.models.project import PROJECT_KINDS
from ichrisbirch.models.project import Project
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

    def test_every_kind_is_represented(self, db):
        """A kind with no seeded project cannot be exercised in the UI or a filtered read."""
        projects.clear(db)
        projects.seed(db, scale=1)
        assert {project.kind for project in db.query(Project).all()} == set(PROJECT_KINDS)

    def test_every_task_has_parent_item(self, db):
        projects.clear(db)
        projects.seed(db, scale=1)
        tasks = db.query(ProjectItemTask).all()
        for task in tasks:
            item = db.query(ProjectItem).filter(ProjectItem.id == task.item_id).first()
            assert item is not None, f'Task {task.id} has no parent item'

    def test_completion_dates_match_completion(self, db):
        """A seeded row with no completion date cannot exercise a date-bounded read."""
        projects.clear(db)
        projects.seed(db, scale=1)

        for item in db.query(ProjectItem).all():
            assert (item.completed_at is not None) == item.completed, f'Item {item.id} disagrees with its own state'
        for task in db.query(ProjectItemTask).all():
            assert (task.completed_at is not None) == task.completed, f'Task {task.id} disagrees with its own state'

    def test_completion_dates_are_spread(self, db):
        """One instant for every finished row makes a range filter untestable by hand."""
        projects.clear(db)
        projects.seed(db, scale=1)

        finished = [item.completed_at for item in db.query(ProjectItem).all() if item.completed]
        assert len(finished) > 1, 'precondition: the seeder makes more than one finished item'
        assert len({stamp.date() for stamp in finished}) > 1
