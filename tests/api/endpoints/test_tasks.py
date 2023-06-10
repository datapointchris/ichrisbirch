import pytest

from ichrisbirch import models
from tests.helpers import show_status_and_response
from tests.testing_data.tasks import TASK_TEST_CREATE_DATA, TASK_TEST_DATA


@pytest.fixture(scope='function')
def test_data():
    """Basic test data"""
    return [models.Task(**record) for record in TASK_TEST_DATA]


@pytest.mark.parametrize('task_id', [1, 2, 3])
def test_read_one_task(insert_test_data, test_api, task_id):
    """Test if able to read one task"""
    response = test_api.get(f'/tasks/{task_id}/')
    assert response.status_code == 200, show_status_and_response(response)


def test_read_many_tasks(insert_test_data, test_api):
    """Test if able to read many tasks"""
    response = test_api.get('/tasks/')
    assert response.status_code == 200, show_status_and_response(response)
    assert len(response.json()) == 3


def test_read_many_tasks_completed(insert_test_data, test_api):
    """Test if able to read many tasks"""
    response = test_api.get('/tasks/?completed_filter=completed')
    assert response.status_code == 200, show_status_and_response(response)
    assert len(response.json()) == 1


def test_read_many_tasks_not_completed(insert_test_data, test_api):
    """Test if able to read many tasks"""
    response = test_api.get('/tasks/?completed_filter=not_completed')
    assert response.status_code == 200, show_status_and_response(response)
    assert len(response.json()) == 2


def test_create_task(insert_test_data, test_api):
    """Test if able to create a task"""
    response = test_api.post('/tasks/', json=TASK_TEST_CREATE_DATA)
    assert response.status_code == 201, show_status_and_response(response)
    assert dict(response.json())['name'] == TASK_TEST_CREATE_DATA['name']

    # Test task was created
    created = test_api.get('/tasks/')
    assert created.status_code == 200, show_status_and_response(created)
    assert len(created.json()) == 4


@pytest.mark.parametrize('task_id', [1, 2, 3])
def test_delete_task(insert_test_data, test_api, task_id):
    """Test if able to delete a task"""
    endpoint = f'/tasks/{task_id}/'
    task = test_api.get(endpoint)
    assert task.status_code == 200, show_status_and_response(task)

    response = test_api.delete(endpoint)
    assert response.status_code == 204, show_status_and_response(response)

    deleted = test_api.get(endpoint)
    assert deleted.status_code == 404, show_status_and_response(deleted)


@pytest.mark.parametrize('task_id', [1, 2, 3])
def test_complete_task(insert_test_data, test_api, task_id):
    """Test if able to complete a task"""
    response = test_api.post(f'/tasks/complete/{task_id}/')
    assert response.status_code == 200, show_status_and_response(response)


def test_read_completed_tasks(insert_test_data, test_api):
    """Test if able to read completed tasks"""
    completed = test_api.get('/tasks/completed/')
    assert completed.status_code == 200, show_status_and_response(completed)
    assert len(completed.json()) == 1


def test_search_task(insert_test_data, test_api):
    """Test search capability"""
    search_term = 'chore'
    search_results = test_api.get(f'/tasks/search/{search_term}')
    assert search_results.status_code == 200, show_status_and_response(search_results)
    assert len(search_results.json()) == 1

    search_term = 'home'
    search_results = test_api.get(f'/tasks/search/{search_term}')
    assert search_results.status_code == 200, show_status_and_response(search_results)
    assert len(search_results.json()) == 2


def test_task_lifecycle(insert_test_data, test_api):
    """Integration test for CRUD lifecylce of a task"""

    # Read all tasks
    all_tasks = test_api.get('/tasks/')
    assert all_tasks.status_code == 200, show_status_and_response(all_tasks)
    assert len(all_tasks.json()) == 3

    # Create new task
    created_task = test_api.post('/tasks/', json=TASK_TEST_CREATE_DATA)
    assert created_task.status_code == 201, show_status_and_response(created_task)
    assert created_task.json()['name'] == TASK_TEST_CREATE_DATA['name']

    # Get created task
    task_id = created_task.json().get('id')
    endpoint = f'/tasks/{task_id}/'
    response_task = test_api.get(endpoint)
    assert response_task.status_code == 200, show_status_and_response(response_task)
    assert response_task.json()['name'] == TASK_TEST_CREATE_DATA['name']

    # Read all tasks with new task
    all_tasks = test_api.get('/tasks/')
    assert all_tasks.status_code == 200, show_status_and_response(all_tasks)
    assert len(all_tasks.json()) == 4

    # Delete Task
    deleted_task = test_api.delete(f'/tasks/{task_id}/')
    assert deleted_task.status_code == 204, show_status_and_response(deleted_task)

    # Make sure it's missing
    missing_task = test_api.get(f'/tasks/{task_id}')
    assert missing_task.status_code == 404, show_status_and_response(missing_task)
