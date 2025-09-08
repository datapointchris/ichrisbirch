"""Tests for the task schema validation.

Tests that the Task, TaskCreate, TaskUpdate, and TaskCompleted schemas properly validate data.
"""

import datetime
from datetime import timedelta

import pytest
from pydantic import ValidationError

from ichrisbirch.models.task import TaskCategory
from ichrisbirch.schemas.task import Task
from ichrisbirch.schemas.task import TaskCompleted
from ichrisbirch.schemas.task import TaskCreate
from ichrisbirch.schemas.task import TaskUpdate


class TestTaskSchema:
    def test_task_create_valid(self):
        """Test creating a valid TaskCreate model."""
        task_data = {'name': 'Test Task', 'notes': 'These are test notes', 'category': TaskCategory.Home, 'priority': 1}
        task = TaskCreate(**task_data)
        assert task.name == 'Test Task'
        assert task.notes == 'These are test notes'
        assert task.category == 'Home'
        assert task.priority == 1

    def test_task_create_without_notes(self):
        """Test creating a task without notes."""
        task_data = {'name': 'Test Task', 'category': TaskCategory.Home, 'priority': 1}
        task = TaskCreate(**task_data)
        assert task.name == 'Test Task'
        assert task.notes is None
        assert task.category == 'Home'
        assert task.priority == 1

    def test_task_create_invalid_missing_fields(self):
        """Test TaskCreate fails with missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(name='Test Task', category=TaskCategory.Home)

        errors = exc_info.value.errors()
        assert any(err['type'] == 'missing' and err['loc'][0] == 'priority' for err in errors)

    def test_task_create_invalid_category(self):
        """Test TaskCreate fails with invalid category."""
        with pytest.raises(ValidationError):
            TaskCreate(name='Test Task', notes='Test notes', category='InvalidCategory', priority=1)

    def test_task_model_valid(self):
        """Test creating a valid Task model."""
        now = datetime.datetime.now()
        task_data = {
            'id': 1,
            'name': 'Test Task',
            'notes': 'These are test notes',
            'category': TaskCategory.Home,
            'priority': 1,
            'add_date': now,
            'complete_date': None,
        }
        task = Task(**task_data)
        assert task.id == 1
        assert task.name == 'Test Task'
        assert task.notes == 'These are test notes'
        assert task.category == 'Home'
        assert task.priority == 1
        assert task.add_date == now
        assert task.complete_date is None

    def test_task_model_with_complete_date(self):
        """Test creating a task with a complete date."""
        now = datetime.datetime.now()
        completed = now + timedelta(days=1)
        task_data = {
            'id': 1,
            'name': 'Test Task',
            'notes': 'These are test notes',
            'category': TaskCategory.Home,
            'priority': 1,
            'add_date': now,
            'complete_date': completed,
        }
        task = Task(**task_data)
        assert task.id == 1
        assert task.complete_date == completed

    def test_task_model_missing_fields(self):
        """Test Task model fails with missing required fields."""
        now = datetime.datetime.now()
        incomplete_data = {'name': 'Test Task', 'category': TaskCategory.Home, 'priority': 1, 'add_date': now}

        with pytest.raises(ValidationError):
            Task(**incomplete_data)

    def test_task_update_valid(self):
        """Test creating a valid TaskUpdate model."""
        task_update = TaskUpdate(name='Updated Task', priority=2)
        assert task_update.name == 'Updated Task'
        assert task_update.priority == 2
        assert task_update.notes is None
        assert task_update.category is None
        assert task_update.add_date is None
        assert task_update.complete_date is None

    def test_task_update_empty(self):
        """Test creating an empty TaskUpdate is valid (all fields optional)."""
        task_update = TaskUpdate()
        assert task_update.name is None
        assert task_update.notes is None
        assert task_update.category is None
        assert task_update.priority is None
        assert task_update.add_date is None
        assert task_update.complete_date is None

    def test_task_completed_valid(self):
        """Test creating a valid TaskCompleted model and verify properties."""
        now = datetime.datetime.now()
        completed = now + timedelta(days=10)

        task_completed_data = {
            'id': 1,
            'name': 'Test Task',
            'notes': 'These are test notes',
            'category': TaskCategory.Home,
            'priority': 1,
            'add_date': now,
            'complete_date': completed,
        }

        task_completed = TaskCompleted(**task_completed_data)
        assert task_completed.id == 1
        assert task_completed.name == 'Test Task'
        assert task_completed.days_to_complete == 10
        assert task_completed.time_to_complete == '1 weeks, 3 days'

    def test_task_completed_same_day(self):
        """Test a task completed on the same day."""
        now = datetime.datetime.now()

        task_completed_data = {
            'id': 1,
            'name': 'Test Task',
            'notes': 'These are test notes',
            'category': TaskCategory.Home,
            'priority': 1,
            'add_date': now,
            'complete_date': now,
        }

        task_completed = TaskCompleted(**task_completed_data)
        assert task_completed.days_to_complete == 1  # Minimum is 1
        assert task_completed.time_to_complete == '0 weeks, 1 days'
