import pytest
from fastapi import status

import tests.util
from ichrisbirch import schemas
from ichrisbirch.models.task import TaskCategory
from tests.utils.database import delete_test_data
from tests.utils.database import insert_test_data


@pytest.fixture(autouse=True)
def insert_testing_data():
    insert_test_data('tasks')
    yield
    delete_test_data('tasks')


def test_index(test_app_logged_in):
    response = test_app_logged_in.get('/tasks/')
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)
    tests.util.verify_page_title(response, 'Priority Tasks')


def test_todo(test_app_logged_in):
    response = test_app_logged_in.get('/tasks/todo/')
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)
    tests.util.verify_page_title(response, 'Outstanding Tasks')


def test_completed(test_app_logged_in):
    response = test_app_logged_in.get('/tasks/completed/')
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)
    tests.util.verify_page_title(response, 'Completed Tasks')


def test_search(test_app_logged_in):
    response = test_app_logged_in.post('/tasks/search/', data={'terms': 'test'}, follow_redirects=True)
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)
    tests.util.verify_page_title(response, 'Tasks Search')


def test_crud_add(test_app_logged_in):
    response = test_app_logged_in.post(
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
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)
    assert len(response.history) == 1
    assert response.request.path == '/tasks/'
    tests.util.verify_page_title(response, 'Priority Tasks')


def test_crud_complete(test_app_logged_in, test_api_logged_in):
    # Get first task ID dynamically
    tasks = test_api_logged_in.get('/tasks/')
    first_id = tasks.json()[0]['id']
    response = test_app_logged_in.post('/tasks/crud/', data={'id': first_id, 'action': 'complete'}, follow_redirects=True)
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)
    assert len(response.history) == 1
    assert response.request.path == '/tasks/'
    tests.util.verify_page_title(response, 'Priority Tasks')


@pytest.mark.parametrize('days', [7, 30])
def test_crud_extend(test_app_logged_in, test_api_logged_in, days):
    """test_api needs to be used because the flask /tasks route always delegates to the api to get specific tasks."""
    # Get first task ID dynamically
    tasks = test_api_logged_in.get('/tasks/')
    task_id = tasks.json()[0]['id']
    task = test_api_logged_in.get(f'/tasks/{task_id}/')
    priority = task.json()['priority']

    response = test_app_logged_in.post('/tasks/crud/', data={'id': task_id, 'action': 'extend', 'days': days}, follow_redirects=True)
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)
    assert len(response.history) == 1
    assert response.request.path == '/tasks/todo/'
    tests.util.verify_page_title(response, 'Outstanding Tasks')

    updated_task = test_api_logged_in.get(f'/tasks/{task_id}/')
    extended_priority = updated_task.json()['priority']
    assert priority + days == extended_priority


def test_crud_delete(test_app_logged_in, test_api_logged_in):
    # Get first task ID dynamically
    tasks = test_api_logged_in.get('/tasks/')
    first_id = tasks.json()[0]['id']
    response = test_app_logged_in.post('/tasks/crud/', data={'id': first_id, 'action': 'delete'}, follow_redirects=True)
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)
    assert len(response.history) == 1
    assert response.request.path == '/tasks/todo/'
    tests.util.verify_page_title(response, 'Outstanding Tasks')


def test_crud_reset_priorities(test_app_logged_in, test_api_logged_in):
    # Get priority of first task dynamically
    tasks = test_api_logged_in.get('/tasks/')
    first_id = tasks.json()[0]['id']
    task_1 = test_api_logged_in.get(f'/tasks/{first_id}/')
    p1 = task_1.json()['priority']

    # Create a task with negative priority
    NEGATIVE_PRIORITY_TASK = schemas.TaskCreate(
        name='Task Negative priority',
        notes='Notes task negative',
        category=TaskCategory.Home,
        priority=-5,
    )
    test_app_logged_in.post('/tasks/crud/', data=NEGATIVE_PRIORITY_TASK.model_dump() | {'action': 'add'})

    # Reset priorities
    response = test_app_logged_in.post('/tasks/crud/', data={'action': 'reset_priorities'}, follow_redirects=True)
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)
    assert len(response.history) == 1
    assert response.request.path == '/tasks/todo/'
    tests.util.verify_page_title(response, 'Outstanding Tasks')

    # Check that the negative priority task updated other task priorities
    task_1_updated = test_api_logged_in.get(f'/tasks/{first_id}/')
    p1_updated = task_1_updated.json()['priority']
    assert p1_updated == p1 + abs(NEGATIVE_PRIORITY_TASK.priority)


def test_crud_reset_priorities_no_negative_priorities(test_app_logged_in, test_api_logged_in):
    # Get priority of first task dynamically
    tasks = test_api_logged_in.get('/tasks/')
    first_id = tasks.json()[0]['id']
    task_1 = test_api_logged_in.get(f'/tasks/{first_id}/')
    p1 = task_1.json()['priority']

    # Reset priorities (no negative priorities)
    response = test_app_logged_in.post('/tasks/crud/', data={'action': 'reset_priorities'}, follow_redirects=True)
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)
    assert len(response.history) == 1
    assert response.request.path == '/tasks/todo/'
    tests.util.verify_page_title(response, 'Outstanding Tasks')

    # Check that the priority has not changed
    task_1_updated = test_api_logged_in.get(f'/tasks/{first_id}/')
    p1_updated = task_1_updated.json()['priority']
    assert p1 == p1_updated


@pytest.mark.parametrize('category', [t.value for t in TaskCategory])
def test_task_categories(test_app_logged_in, category):
    response = test_app_logged_in.post(
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
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)
    assert len(response.history) == 1
    assert response.request.path == '/tasks/'
    tests.util.verify_page_title(response, 'Priority Tasks')


def test_completed_shows_data_not_error(test_app_logged_in):
    """Verify completed tasks page shows actual data, not silenced error.

    Test data has one completed task (2020-04-20). When using 'all' filter
    (no date params), the page should show:
    - Average Completion Time (indicates data was found)
    - NOT 'No completed tasks for time period' (indicates error or empty)

    This test catches the bug where API errors are silently swallowed and
    users see 'No completed tasks' instead of helpful error feedback.
    """
    # POST with 'all' filter to bypass date filtering entirely
    response = test_app_logged_in.post('/tasks/completed/', data={'filter': 'all'})
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)
    tests.util.verify_page_title(response, 'Completed Tasks')

    # Verify we got actual data, not an error message
    response_text = response.data.decode('utf-8')

    # Should see completion time stats (indicates data was found and processed)
    assert 'Average Completion Time' in response_text, (
        'Expected "Average Completion Time" in response - indicates data was found. '
        'If missing, API may have returned error that was silently swallowed.'
    )

    # Should NOT see the "no completed tasks" error message
    assert 'No completed tasks for time period' not in response_text, (
        'Found "No completed tasks for time period" error message. '
        'Test data has a completed task, so this indicates API error was silently swallowed.'
    )
