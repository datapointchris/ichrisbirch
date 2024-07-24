import pytest
from fastapi import status

import tests.util
from ichrisbirch import schemas
from ichrisbirch.models.task import TaskCategory
from tests.util import show_status_and_response


@pytest.fixture(autouse=True)
def insert_testing_data():
    tests.util.insert_test_data('tasks')


NEW_TASK = schemas.TaskCreate(
    name='Task 4 Computer with notes priority 3',
    notes='Notes task 4',
    category=TaskCategory.Computer,
    priority=3,
)


@pytest.mark.parametrize('task_id', [1, 2, 3])
def test_read_one_task(test_api, task_id):
    response = test_api.get(f'/tasks/{task_id}/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


def test_read_many_tasks(test_api):
    response = test_api.get('/tasks/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 3


def test_read_many_tasks_completed(test_api):
    response = test_api.get('/tasks/completed/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 1


def test_read_many_tasks_not_completed(test_api):
    response = test_api.get('/tasks/todo/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 2


def test_create_task(test_api):
    response = test_api.post('/tasks/', json=NEW_TASK.model_dump())
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    assert dict(response.json())['name'] == NEW_TASK.name

    # Test task was created
    created = test_api.get('/tasks/')
    assert created.status_code == status.HTTP_200_OK, show_status_and_response(created)
    assert len(created.json()) == 4


@pytest.mark.parametrize('task_id', [1, 2, 3])
def test_delete_task(test_api, task_id):
    endpoint = f'/tasks/{task_id}/'
    task = test_api.get(endpoint)
    assert task.status_code == status.HTTP_200_OK, show_status_and_response(task)

    response = test_api.delete(endpoint)
    assert response.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(response)

    deleted = test_api.get(endpoint)
    assert deleted.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(deleted)


@pytest.mark.parametrize('task_id', [1, 2, 3])
def test_complete_task(test_api, task_id):
    response = test_api.patch(f'/tasks/{task_id}/complete/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


def test_read_completed_tasks(test_api):
    completed = test_api.get('/tasks/completed/')
    assert completed.status_code == status.HTTP_200_OK, show_status_and_response(completed)
    assert len(completed.json()) == 1


def test_search_task(test_api):
    search_term = 'chore'
    search_results = test_api.get('/tasks/search/', params={'q': search_term})
    assert search_results.status_code == status.HTTP_200_OK, show_status_and_response(search_results)
    assert len(search_results.json()) == 1

    search_term = 'home'
    search_results = test_api.get('/tasks/search/', params={'q': search_term})
    assert search_results.status_code == status.HTTP_200_OK, show_status_and_response(search_results)
    assert len(search_results.json()) == 2


def test_task_lifecycle(test_api):
    """Integration test for CRUD lifecylce of a task."""

    # Read all tasks
    all_tasks = test_api.get('/tasks/')
    assert all_tasks.status_code == status.HTTP_200_OK, show_status_and_response(all_tasks)
    assert len(all_tasks.json()) == 3

    created_task = test_api.post('/tasks/', json=NEW_TASK.model_dump())
    assert created_task.status_code == status.HTTP_201_CREATED, show_status_and_response(created_task)
    assert created_task.json()['name'] == NEW_TASK.name

    # Get created task
    task_id = created_task.json().get('id')
    endpoint = f'/tasks/{task_id}/'
    response_task = test_api.get(endpoint)
    assert response_task.status_code == status.HTTP_200_OK, show_status_and_response(response_task)
    assert response_task.json()['name'] == NEW_TASK.name

    # Read all tasks with new task
    all_tasks = test_api.get('/tasks/')
    assert all_tasks.status_code == status.HTTP_200_OK, show_status_and_response(all_tasks)
    assert len(all_tasks.json()) == 4

    # Delete Task
    deleted_task = test_api.delete(f'/tasks/{task_id}/')
    assert deleted_task.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(deleted_task)

    # Make sure it's missing
    missing_task = test_api.get(f'/tasks/{task_id}')
    assert missing_task.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(missing_task)


@pytest.mark.parametrize('category', list(TaskCategory))
def test_task_categories(test_api, category):
    test_task = schemas.TaskCreate(
        name='Task 4 Computer with notes priority 3',
        notes='Notes task 4',
        category=category,
        priority=3,
    )
    created_task = test_api.post('/tasks/', json=test_task.model_dump())
    assert created_task.status_code == status.HTTP_201_CREATED, show_status_and_response(created_task)
    assert created_task.json()['name'] == test_task.name


def test_reset_priorities(test_api):
    # Priority of first task
    task_1 = test_api.get('/tasks/1/')
    p1 = task_1.json()['priority']

    # Create a task with negative priority
    NEGATIVE_PRIORITY_TASK = schemas.TaskCreate(
        name='Task Negative priority',
        notes='Notes task negative',
        category=TaskCategory.Home,
        priority=-5,
    )
    test_api.post('/tasks/', json=NEGATIVE_PRIORITY_TASK.model_dump())

    # Reset priorities
    response = test_api.post('/tasks/reset-priorities/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    # One of the 3 original tasks is completed, so 2 tasks + 1 new task = 3
    assert response.json().get('message') == 'Reset priorities for 3 tasks'

    # Check that the negative priority task updated other task priorities
    task_1_updated = test_api.get('/tasks/1/')
    p1_updated = task_1_updated.json()['priority']
    assert p1_updated == p1 + abs(NEGATIVE_PRIORITY_TASK.priority)


def test_reset_priorities_no_negative_priorities(test_api):
    response = test_api.post('/tasks/reset-priorities/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert response.json().get('message') == 'No negative priorities to reset'
