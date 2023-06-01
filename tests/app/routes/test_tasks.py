from ichrisbirch.app.routes.tasks import TASKS_URL
from ichrisbirch.models.task import TaskCategory


def test_index(test_app):
    response = test_app.get(TASKS_URL + '/')
    assert response.status_code == 200
    assert b'<title>Priority Tasks</title>' in response.data


def test_all(test_app):
    response = test_app.get(TASKS_URL + '/all/')
    assert response.status_code == 200
    assert b'<title>All Tasks</title>' in response.data


def test_completed(test_app):
    response = test_app.get(TASKS_URL + '/completed/')
    assert response.status_code == 200
    assert b'Completed Tasks' in response.data


def test_crud_add(test_app):
    data = {
        'name': 'Test Task 1',
        'category': TaskCategory.Chore.value,
        'priority': 10,
        'notes': 'Test Notes',
        'method': 'add',
    }
    response = test_app.post(TASKS_URL + '/crud/', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert len(response.history) == 1
    assert response.request.path == '/tasks/'
    assert b'<title>Priority Tasks</title>' in response.data


def test_crud_complete(test_app):
    data = {
        'id': 1,
        'method': 'complete',
    }
    response = test_app.post('/tasks/crud/', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert len(response.history) == 1
    assert response.request.path == '/tasks/'
    assert b'<title>Priority Tasks</title>' in response.data


def test_crud_delete(test_app):
    data = {
        'id': 1,
        'method': 'delete',
    }
    response = test_app.post('/tasks/crud/', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert len(response.history) == 1
    assert response.request.path == '/tasks/all/'
    assert b'All Tasks' in response.data


def test_crud_search(test_app):
    data = {
        'terms': 'test',
        'method': 'search',
    }
    response = test_app.post('/tasks/crud/', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b'<title>Tasks Search</title>' in response.data
