from fastapi import status

from ichrisbirch.models.task import TaskCategory
from tests.helpers import show_status_and_response


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


def test_crud_delete(test_app):
    response = test_app.post('/tasks/crud/', data={'id': 1, 'action': 'delete'}, follow_redirects=True)
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.history) == 1
    assert response.request.path == '/tasks/todo/'
    assert b'Outstanding Tasks' in response.data


def test_crud_search(test_app):
    response = test_app.post('/tasks/search/', data={'terms': 'test'}, follow_redirects=True)
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>Tasks Search</title>' in response.data
