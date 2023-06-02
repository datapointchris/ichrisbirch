from ichrisbirch.models.autotask import TaskFrequency
from ichrisbirch.models.task import TaskCategory


def test_index(postgres_testdb_in_docker, test_api, test_app):
    """Test the index page"""
    response = test_app.get('/autotasks/')
    assert response.status_code == 200
    assert b'<title>AutoTasks</title>' in response.data


def test_crud_add(postgres_testdb_in_docker, test_api, test_app):
    """Test add a new task"""
    data = {
        'name': 'AutoTask 1',
        'category': TaskCategory.Chore.value,
        'priority': 10,
        'notes': 'Description 1',
        'frequency': TaskFrequency.Weekly.value,
        'method': 'add',
    }
    response = test_app.post('/autotasks/crud/', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert len(response.history) == 1
    assert response.request.path == '/autotasks/'
    assert b'<title>AutoTasks</title>' in response.data


def test_crud_delete(postgres_testdb_in_docker, test_api, test_app):
    """Test delete a task"""
    data = {
        'id': 1,
        'method': 'delete',
    }
    response = test_app.post('/autotasks/crud/', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert len(response.history) == 1
    assert response.request.path == '/autotasks/'
    assert b'<title>AutoTasks</title>' in response.data
