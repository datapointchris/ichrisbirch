"""Tests for the task schema validation.

Tests that the Task, TaskCreate, TaskUpdate, and TaskCompleted schemas properly validate data.
"""

import datetime
from datetime import timedelta

import pytest
from pydantic import ValidationError

from ichrisbirch.schemas.task import Task
from ichrisbirch.schemas.task import TaskCompleted
from ichrisbirch.schemas.task import TaskCreate
from ichrisbirch.schemas.task import TaskUpdate


class TestTaskSchema:
    def test_task_create_valid(self):
        task = TaskCreate(name='Test Task', notes='These are test notes', category='Home', window_days=4)
        assert task.name == 'Test Task'
        assert task.notes == 'These are test notes'
        assert task.category == 'Home'
        assert task.window_days == 4

    def test_task_create_leaves_the_window_to_the_category(self):
        task = TaskCreate(name='Test Task', category='Home')
        assert task.window_days is None
        assert task.pinned is False

    @pytest.mark.parametrize('window_days', [0, -3])
    def test_task_create_refuses_a_window_below_one_day(self, window_days):
        with pytest.raises(ValidationError):
            TaskCreate(name='Test Task', category='Home', window_days=window_days)

    def test_task_create_invalid_missing_fields(self):
        """Test TaskCreate fails when truly required fields (name, category) are missing."""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(name='Test Task')

        errors = exc_info.value.errors()
        assert any(err['type'] == 'missing' and err['loc'][0] == 'category' for err in errors)

    def test_task_model_valid(self):
        now = datetime.datetime.now(datetime.UTC)
        task = Task(
            id=1,
            name='Test Task',
            notes='These are test notes',
            category='Home',
            rank_at=now + timedelta(days=60),
            window_days=60,
            pinned=False,
            add_date=now,
        )
        assert task.id == 1
        assert task.rank_at == now + timedelta(days=60)
        assert task.complete_date is None
        assert task.drop_date is None

    def test_task_model_missing_fields(self):
        now = datetime.datetime.now(datetime.UTC)
        with pytest.raises(ValidationError):
            Task(name='Test Task', category='Home', add_date=now)

    def test_task_update_valid(self):
        task_update = TaskUpdate(name='Updated Task', pinned=True)
        assert task_update.name == 'Updated Task'
        assert task_update.pinned is True
        assert task_update.model_dump(exclude_unset=True) == {'name': 'Updated Task', 'pinned': True}

    def test_task_update_empty(self):
        """Test creating an empty TaskUpdate is valid (all fields optional)."""
        assert TaskUpdate().model_dump(exclude_unset=True) == {}

    def test_task_completed_valid(self):
        """Test creating a valid TaskCompleted model and verify properties."""
        now = datetime.datetime.now(datetime.UTC)
        task_completed = TaskCompleted(
            id=1,
            name='Test Task',
            notes='These are test notes',
            category='Home',
            window_days=60,
            add_date=now,
            complete_date=now + timedelta(days=10),
        )
        assert task_completed.days_to_complete == 10
        assert task_completed.time_to_complete == '1 weeks, 3 days'

    def test_task_completed_same_day(self):
        """Test a task completed on the same day."""
        now = datetime.datetime.now(datetime.UTC)
        task_completed = TaskCompleted(id=1, name='Test Task', category='Home', window_days=60, add_date=now, complete_date=now)
        assert task_completed.days_to_complete == 1  # Minimum is 1
        assert task_completed.time_to_complete == '0 weeks, 1 days'
