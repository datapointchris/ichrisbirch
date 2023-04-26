import json

import pytest

from ichrisbirch import models
from ichrisbirch.api.endpoints import tasks


@pytest.fixture(scope='module')
def base_test_data():
    """Basic test data"""
    return [
        {
            'name': 'Task 1 Chore with notes priority 5 not completed',
            'notes': 'Notes for task 1',
            'category': 'Chore',
            'priority': 5,
        },
        {
            'name': 'Task 2 Home without notes priority 10 not completed',
            'notes': None,
            'category': 'Chore',
            'priority': 10,
        },
        {
            'name': 'Task 3 Home with notes priority 15 completed',
            'notes': 'Notes for task 3',
            'category': 'Home',
            'priority': 15,
            'complete_date': '2020-04-20 03:03:39.050648+00:00',
        },
    ]


test_data_for_create = [
    {'name': 'Task 4 Computer with notes priority 3', 'notes': 'Notes task 4', 'category': 'Computer', 'priority': 3},
    {'name': 'Task 5 Chore without notes priority 20', 'notes': None, 'category': 'Chore', 'priority': 20},
]


@pytest.fixture(scope='module')
def data_model():
    """Returns the SQLAlchemy model to use for the data"""
    return models.Task


@pytest.fixture(scope='module')
def router():
    """Returns the API router to use for this test module"""
    return tasks.router


@pytest.mark.parametrize('task_id', [1, 2, 3])
def test_read_one_task(postgres_testdb_in_docker, insert_test_data, test_app, task_id):
    """Test if able to read one task"""
    response = test_app.get(f'/tasks/{task_id}/')
    assert response.status_code == 200


def test_read_many_tasks(postgres_testdb_in_docker, insert_test_data, test_app):
    """Test if able to read many tasks"""
    response = test_app.get('/tasks/')
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_read_many_tasks_completed(postgres_testdb_in_docker, insert_test_data, test_app):
    """Test if able to read many tasks"""
    response = test_app.get('/tasks/?completed_filter=completed')
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_read_many_tasks_not_completed(postgres_testdb_in_docker, insert_test_data, test_app):
    """Test if able to read many tasks"""
    response = test_app.get('/tasks/?completed_filter=not_completed')
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.parametrize('test_task', test_data_for_create)
def test_create_task(postgres_testdb_in_docker, insert_test_data, test_app, test_task):
    """Test if able to create a task"""
    response = test_app.post('/tasks/', data=json.dumps(test_task))
    assert response.status_code == 200
    assert dict(response.json())['name'] == test_task['name']

    # Test task was created
    response = test_app.get('/tasks/')
    assert response.status_code == 200
    assert len(response.json()) == 4


@pytest.mark.parametrize('task_id', [1, 2, 3])
def test_delete_task(postgres_testdb_in_docker, insert_test_data, test_app, task_id):
    """Test if able to delete a task"""
    endpoint = f'/tasks/{task_id}/'
    task = test_app.get(endpoint)
    response = test_app.delete(endpoint)
    deleted = test_app.get(endpoint)
    assert response.status_code == 200
    assert response.json() == task.json()
    assert deleted.status_code == 404


@pytest.mark.parametrize('task_id', [1, 2, 3])
def test_complete_task(postgres_testdb_in_docker, insert_test_data, test_app, task_id):
    """Test if able to complete a task"""
    response = test_app.post(f'/tasks/complete/{task_id}/')
    assert response.status_code == 200


def test_read_completed_tasks(postgres_testdb_in_docker, insert_test_data, test_app):
    """Test if able to read completed tasks"""
    completed = test_app.get('/tasks/completed/')
    assert completed.status_code == 200
    assert len(completed.json()) == 1


@pytest.mark.parametrize('test_task', test_data_for_create)
def test_task_lifecycle(postgres_testdb_in_docker, insert_test_data, test_app, test_task):
    """Integration test for CRUD lifecylce of a task"""

    # Create new task
    created_task = test_app.post('/tasks/', data=json.dumps(test_task))
    assert created_task.status_code == 200
    assert created_task.json()['name'] == test_task['name']

    # Read all tasks
    all_tasks = test_app.get('/tasks/')
    assert all_tasks.status_code == 200
    assert len(all_tasks.json()) == 4

    # Get created task
    task_id = created_task.json().get('id')
    endpoint = f'/tasks/{task_id}/'
    response_task = test_app.get(endpoint)
    assert response_task.status_code == 200
    assert response_task.json()['name'] == test_task['name']

    # Delete Task
    deleted_task = test_app.delete(f'/tasks/{task_id}/').json()
    assert deleted_task['name'] == test_task['name']

    # Make sure it's missing
    missing_task = test_app.get(f'/tasks/{task_id}')
    assert missing_task.status_code == 404
