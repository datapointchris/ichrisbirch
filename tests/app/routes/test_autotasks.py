import pytest

from ichrisbirch.app.main import create_app
from ichrisbirch.app.routes.autotasks import AUTOTASKS_URL
from ichrisbirch.config import get_settings
from ichrisbirch.models.autotask import TaskFrequency
from ichrisbirch.models.task import TaskCategory

settings = get_settings()


@pytest.fixture
def app():
    app = create_app()
    app.config.update({'TESTING': True})
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_index(client):
    response = client.get(AUTOTASKS_URL + '/')
    assert response.status_code == 200
    assert b'<title>AutoTasks</title>' in response.data


def test_crud_add(client):
    data = {
        'name': 'AutoTask 1',
        'category': TaskCategory.Chore.value,
        'priority': 10,
        'notes': 'Description 1',
        'frequency': TaskFrequency.Weekly.value,
        'method': 'add',
    }
    response = client.post(AUTOTASKS_URL + '/crud/', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert len(response.history) == 1
    assert response.request.path == '/autotasks/'
    assert b'<title>AutoTasks</title>' in response.data


def test_crud_delete(client):
    data = {
        'id': 1,
        'method': 'delete',
    }
    response = client.post(AUTOTASKS_URL + '/crud/', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert len(response.history) == 1
    assert response.request.path == '/autotasks/'
