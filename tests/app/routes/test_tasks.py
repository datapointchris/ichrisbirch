from ichrisbirch.app.routes.tasks import TASKS_URL
from tests.helpers import show_status_and_response
from tests.testing_data.tasks import CREATE_DATA


def test_index(test_app):
    response = test_app.get(TASKS_URL + '/')
    assert response.status_code == 200, show_status_and_response(response)
    assert b'<title>Priority Tasks</title>' in response.data


def test_all(test_app):
    response = test_app.get(TASKS_URL + '/all/')
    assert response.status_code == 200, show_status_and_response(response)
    assert b'<title>All Tasks</title>' in response.data


def test_completed(test_app):
    response = test_app.get(TASKS_URL + '/completed/')
    assert response.status_code == 200, show_status_and_response(response)
    assert b'Completed Tasks' in response.data


def test_crud_add(test_app):
    response = test_app.post(TASKS_URL + '/crud/', data=CREATE_DATA | {'method': 'add'}, follow_redirects=True)
    assert response.status_code == 200, show_status_and_response(response)
    assert len(response.history) == 1
    assert response.request.path == '/tasks/'
    assert b'<title>Priority Tasks</title>' in response.data


def test_crud_complete(test_app):
    response = test_app.post('/tasks/crud/', data={'id': 1, 'method': 'complete'}, follow_redirects=True)
    assert response.status_code == 200, show_status_and_response(response)
    assert len(response.history) == 1
    assert response.request.path == '/tasks/'
    assert b'<title>Priority Tasks</title>' in response.data


def test_crud_delete(test_app):
    response = test_app.post('/tasks/crud/', data={'id': 1, 'method': 'delete'}, follow_redirects=True)
    assert response.status_code == 200, show_status_and_response(response)
    assert len(response.history) == 1
    assert response.request.path == '/tasks/all/'
    assert b'All Tasks' in response.data


def test_crud_search(test_app):
    response = test_app.post('/tasks/crud/', data={'terms': 'test', 'method': 'search'}, follow_redirects=True)
    assert response.status_code == 200, show_status_and_response(response)
    assert b'<title>Tasks Search</title>' in response.data
