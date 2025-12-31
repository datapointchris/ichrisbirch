import pytest
from fastapi import status

from ichrisbirch import schemas
from ichrisbirch.models.task import TaskCategory
from tests.util import show_status_and_response
from tests.utils.database import insert_test_data_transactional

from .crud_test import ApiCrudTester

ENDPOINT = '/tasks/'
NEW_OBJ = schemas.TaskCreate(
    name='Task 4 Computer with notes priority 3',
    notes='Notes task 4',
    category=TaskCategory.Computer,
    priority=3,
)


@pytest.fixture
def task_crud_tester(txn_api_logged_in):
    """Provide ApiCrudTester with transactional test data."""
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'tasks')
    crud_tester = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ)
    return client, crud_tester


def test_read_one(task_crud_tester):
    client, crud_tester = task_crud_tester
    crud_tester.test_read_one(client)


def test_read_many(task_crud_tester):
    client, crud_tester = task_crud_tester
    crud_tester.test_read_many(client)


def test_create(task_crud_tester):
    client, crud_tester = task_crud_tester
    crud_tester.test_create(client)


def test_delete(task_crud_tester):
    client, crud_tester = task_crud_tester
    crud_tester.test_delete(client)


def test_lifecycle(task_crud_tester):
    client, crud_tester = task_crud_tester
    crud_tester.test_lifecycle(client)


def test_read_many_tasks_completed(task_crud_tester):
    client, _ = task_crud_tester
    response = client.get('/tasks/completed/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 1


def test_read_many_tasks_not_completed(task_crud_tester):
    client, _ = task_crud_tester
    response = client.get(f'{ENDPOINT}todo/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 2


def test_complete_task(task_crud_tester):
    client, crud_tester = task_crud_tester
    first_id = crud_tester.item_id_by_position(client, position=1)
    response = client.patch(f'{ENDPOINT}{first_id}/complete/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


def test_read_completed_tasks(task_crud_tester):
    client, _ = task_crud_tester
    completed = client.get('/tasks/completed/')
    assert completed.status_code == status.HTTP_200_OK, show_status_and_response(completed)
    assert len(completed.json()) == 1


def test_search_task(task_crud_tester):
    client, _ = task_crud_tester
    search_term = 'chore'
    search_results = client.get('/tasks/search/', params={'q': search_term})
    assert search_results.status_code == status.HTTP_200_OK, show_status_and_response(search_results)
    assert len(search_results.json()) == 1

    search_term = 'home'
    search_results = client.get('/tasks/search/', params={'q': search_term})
    assert search_results.status_code == status.HTTP_200_OK, show_status_and_response(search_results)
    assert len(search_results.json()) == 2


@pytest.mark.parametrize('category', list(TaskCategory))
def test_task_categories(txn_api_logged_in, category):
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'tasks')
    test_task = schemas.TaskCreate(
        name='Task 4 Computer with notes priority 3',
        notes='Notes task 4',
        category=category,
        priority=3,
    )
    created_task = client.post(ENDPOINT, json=test_task.model_dump())
    assert created_task.status_code == status.HTTP_201_CREATED, show_status_and_response(created_task)
    assert created_task.json()['name'] == test_task.name


def test_reset_priorities(task_crud_tester):
    client, crud_tester = task_crud_tester
    # Priority of first task
    first_id = crud_tester.item_id_by_position(client, position=1)
    task_1 = client.get(f'/tasks/{first_id}/')
    p1 = task_1.json()['priority']

    # Create a task with negative priority
    NEGATIVE_PRIORITY_TASK = schemas.TaskCreate(
        name='Task Negative priority',
        notes='Notes task negative',
        category=TaskCategory.Home,
        priority=-5,
    )
    client.post(ENDPOINT, json=NEGATIVE_PRIORITY_TASK.model_dump())

    # Reset priorities
    response = client.post('/tasks/reset-priorities/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    # One of the 3 original tasks is completed, so 2 tasks + 1 new task = 3
    assert response.json().get('message') == 'Reset priorities for 3 tasks'

    # Check that the negative priority task updated other task priorities
    task_1_updated = client.get(f'/tasks/{first_id}/')
    p1_updated = task_1_updated.json()['priority']
    assert p1_updated == p1 + abs(NEGATIVE_PRIORITY_TASK.priority)


def test_reset_priorities_no_negative_priorities(task_crud_tester):
    client, _ = task_crud_tester
    response = client.post('/tasks/reset-priorities/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert response.json().get('message') == 'No negative priorities to reset'
