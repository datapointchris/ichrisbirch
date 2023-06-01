from ichrisbirch.app.routes.autotasks import AUTOTASKS_URL
from ichrisbirch.models.autotask import TaskFrequency
from ichrisbirch.models.task import TaskCategory


def test_index(test_app):
    response = test_app.get(AUTOTASKS_URL + '/')
    assert response.status_code == 200
    assert b'<title>AutoTasks</title>' in response.data


def test_crud_add(test_app):
    data = {
        'name': 'AutoTask 1',
        'category': TaskCategory.Chore.value,
        'priority': 10,
        'notes': 'Description 1',
        'frequency': TaskFrequency.Weekly.value,
        'method': 'add',
    }
    response = test_app.post(AUTOTASKS_URL + '/crud/', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert len(response.history) == 1
    assert response.request.path == '/autotasks/'
    assert b'<title>AutoTasks</title>' in response.data


def test_crud_delete(test_app):
    data = {
        'id': 1,
        'method': 'delete',
    }
    response = test_app.post(AUTOTASKS_URL + '/crud/', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert len(response.history) == 1
    assert response.request.path == '/autotasks/'
    assert b'<title>AutoTasks</title>' in response.data
