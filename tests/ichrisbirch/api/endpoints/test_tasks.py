import pytest
from fastapi import status

from ichrisbirch import schemas
from ichrisbirch.models.task import TaskCategory
from tests.util import show_status_and_response
from tests.utils.database import delete_test_data
from tests.utils.database import insert_test_data

from .crud_test import ApiCrudTester


@pytest.fixture(autouse=True)
def insert_testing_data():
    insert_test_data('tasks')
    yield
    delete_test_data('tasks')


ENDPOINT = '/tasks/'
NEW_OBJ = schemas.TaskCreate(
    name='Task 4 Computer with notes priority 3',
    notes='Notes task 4',
    category=TaskCategory.Computer,
    priority=3,
)
crud_tests = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ)


def test_read_one(test_api_logged_in):
    crud_tests.test_read_one(test_api_logged_in)


def test_read_many(test_api_logged_in):
    crud_tests.test_read_many(test_api_logged_in)


def test_create(test_api_logged_in):
    crud_tests.test_create(test_api_logged_in)


def test_delete(test_api_logged_in):
    crud_tests.test_delete(test_api_logged_in)


def test_lifecycle(test_api_logged_in):
    crud_tests.test_lifecycle(test_api_logged_in)


def test_read_many_tasks_completed(test_api_logged_in):
    response = test_api_logged_in.get('/tasks/completed/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 1


def test_read_many_tasks_not_completed(test_api_logged_in):
    response = test_api_logged_in.get(f'{ENDPOINT}todo/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 2


def test_complete_task(test_api_logged_in):
    first_id = crud_tests.item_id_by_position(test_api_logged_in, position=1)
    response = test_api_logged_in.patch(f'{ENDPOINT}{first_id}/complete/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


def test_read_completed_tasks(test_api_logged_in):
    completed = test_api_logged_in.get('/tasks/completed/')
    assert completed.status_code == status.HTTP_200_OK, show_status_and_response(completed)
    assert len(completed.json()) == 1


def test_search_task(test_api_logged_in):
    search_term = 'chore'
    search_results = test_api_logged_in.get('/tasks/search/', params={'q': search_term})
    assert search_results.status_code == status.HTTP_200_OK, show_status_and_response(search_results)
    assert len(search_results.json()) == 1

    search_term = 'home'
    search_results = test_api_logged_in.get('/tasks/search/', params={'q': search_term})
    assert search_results.status_code == status.HTTP_200_OK, show_status_and_response(search_results)
    assert len(search_results.json()) == 2


@pytest.mark.parametrize('category', list(TaskCategory))
def test_task_categories(test_api_logged_in, category):
    test_task = schemas.TaskCreate(
        name='Task 4 Computer with notes priority 3',
        notes='Notes task 4',
        category=category,
        priority=3,
    )
    created_task = test_api_logged_in.post(ENDPOINT, json=test_task.model_dump())
    assert created_task.status_code == status.HTTP_201_CREATED, show_status_and_response(created_task)
    assert created_task.json()['name'] == test_task.name


def test_reset_priorities(test_api_logged_in):
    # Priority of first task
    first_id = crud_tests.item_id_by_position(test_api_logged_in, position=1)
    task_1 = test_api_logged_in.get(f'/tasks/{first_id}/')
    p1 = task_1.json()['priority']

    # Create a task with negative priority
    NEGATIVE_PRIORITY_TASK = schemas.TaskCreate(
        name='Task Negative priority',
        notes='Notes task negative',
        category=TaskCategory.Home,
        priority=-5,
    )
    test_api_logged_in.post(ENDPOINT, json=NEGATIVE_PRIORITY_TASK.model_dump())

    # Reset priorities
    response = test_api_logged_in.post('/tasks/reset-priorities/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    # One of the 3 original tasks is completed, so 2 tasks + 1 new task = 3
    assert response.json().get('message') == 'Reset priorities for 3 tasks'

    # Check that the negative priority task updated other task priorities
    task_1_updated = test_api_logged_in.get(f'/tasks/{first_id}/')
    p1_updated = task_1_updated.json()['priority']
    assert p1_updated == p1 + abs(NEGATIVE_PRIORITY_TASK.priority)


def test_reset_priorities_no_negative_priorities(test_api_logged_in):
    response = test_api_logged_in.post('/tasks/reset-priorities/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert response.json().get('message') == 'No negative priorities to reset'
