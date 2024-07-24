import pytest
from fastapi import status

import tests.util
from ichrisbirch import schemas
from ichrisbirch.models.task import TaskCategory
from tests.util import show_status_and_response


@pytest.fixture(autouse=True)
def insert_testing_data():
    tests.util.insert_test_data('tasks')


def test_index(test_app):
    response = test_app.get('/tasks/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>Priority Tasks</title>' in response.data


def test_todo(test_app):
    response = test_app.get('/tasks/todo/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>Outstanding Tasks</title>' in response.data


def test_completed(test_app):
    response = test_app.get('/tasks/completed/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'Completed Tasks' in response.data


def test_search(test_app):
    response = test_app.post('/tasks/search/', data={'terms': 'test'}, follow_redirects=True)
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>Tasks Search</title>' in response.data


def test_crud_add(test_app):
    response = test_app.post(
        '/tasks/crud/',
        data=dict(
            name='Task 4 Computer with notes priority 3',
            notes='Notes task 4',
            category=TaskCategory.Computer.value,
            priority=3,
            action='add',
        ),
        follow_redirects=True,
    )
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.history) == 1
    assert response.request.path == '/tasks/'
    assert b'<title>Priority Tasks</title>' in response.data


def test_crud_complete(test_app):
    response = test_app.post('/tasks/crud/', data={'id': 1, 'action': 'complete'}, follow_redirects=True)
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.history) == 1
    assert response.request.path == '/tasks/'
    assert b'<title>Priority Tasks</title>' in response.data


@pytest.mark.parametrize('days', [7, 30])
def test_crud_extend(test_app, test_api, days):
    """test_api needs to be used because the flask /tasks route always delegates to the api to get specific tasks."""
    task_id = 1
    task = test_api.get(f'/tasks/{task_id}/')
    priority = task.json()['priority']

    extend_response = test_app.post(
        '/tasks/crud/', data={'id': 1, 'action': 'extend', 'days': days}, follow_redirects=True
    )
    assert extend_response.status_code == status.HTTP_200_OK, show_status_and_response(extend_response)
    assert len(extend_response.history) == 1
    assert extend_response.request.path == '/tasks/todo/'
    assert b'<title>Outstanding Tasks</title>' in extend_response.data

    updated_task = test_api.get(f'/tasks/{task_id}/')
    extended_priority = updated_task.json()['priority']
    assert priority + days == extended_priority


def test_crud_delete(test_app):
    response = test_app.post('/tasks/crud/', data={'id': 1, 'action': 'delete'}, follow_redirects=True)
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.history) == 1
    assert response.request.path == '/tasks/todo/'
    assert b'Outstanding Tasks' in response.data


def test_crud_reset_priorities(test_app, test_api):
    # Get priority of first task
    task_1 = test_api.get('/tasks/1/')
    p1 = task_1.json()['priority']

    # Create a task with negative priority
    NEGATIVE_PRIORITY_TASK = schemas.TaskCreate(
        name='Task Negative priority',
        notes='Notes task negative',
        category=TaskCategory.Home,
        priority=-5,
    )
    test_app.post('/tasks/crud/', data=NEGATIVE_PRIORITY_TASK.model_dump() | {'action': 'add'})

    # Reset priorities
    response = test_app.post('/tasks/crud/', data={'action': 'reset_priorities'}, follow_redirects=True)
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.history) == 1
    assert response.request.path == '/tasks/todo/'
    assert b'Outstanding Tasks' in response.data

    # Check that the negative priority task updated other task priorities
    task_1_updated = test_api.get('/tasks/1/')
    p1_updated = task_1_updated.json()['priority']
    assert p1_updated == p1 + abs(NEGATIVE_PRIORITY_TASK.priority)


def test_crud_reset_priorities_no_negative_priorities(test_app, test_api):
    # Get priority of first task
    task_1 = test_api.get('/tasks/1/')
    p1 = task_1.json()['priority']

    # Reset priorities (no negative priorities)
    response = test_app.post('/tasks/crud/', data={'action': 'reset_priorities'}, follow_redirects=True)
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.history) == 1
    assert response.request.path == '/tasks/todo/'
    assert b'Outstanding Tasks' in response.data

    # Check that the priority has not changed
    task_1_updated = test_api.get('/tasks/1/')
    p1_updated = task_1_updated.json()['priority']
    assert p1 == p1_updated


@pytest.mark.parametrize('category', [t.value for t in TaskCategory])
def test_task_categories(test_app, category):
    response = test_app.post(
        '/tasks/crud/',
        data=dict(
            name='Task 4 Computer with notes priority 3',
            notes='Notes task 4',
            category=category,
            priority=3,
            action='add',
        ),
        follow_redirects=True,
    )
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.history) == 1
    assert response.request.path == '/tasks/'
    assert b'<title>Priority Tasks</title>' in response.data
