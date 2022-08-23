import os

os.environ['ENVIRONMENT'] = 'development'

import requests
import pytest
import sqlite3
from backend.api.main import app
from backend.common.config import get_config_for_environment
import json


config = get_config_for_environment('development')
ENDPOINT = '/tasks/'
# ENDPOINT_URL = config.API_URL + ENDPOINT
ENDPOINT_URL = 'http://localhost:8000' + ENDPOINT
TEST_TASK_IDS = (1, 10, 50, 100, 250, 500, 1000)


def create_tasks_test_database(num: int = 10):
    return [
        {"name": f"task-{num}", "category": f"category-{num}", "priority": num}
        for num in range(num)
    ]


TASKS_TO_CREATE = create_tasks_test_database()


@pytest.fixture(autouse=True)
def disable_network_calls(monkeypatch):
    def disabled():
        raise RuntimeError("Network access not allowed during testing!")

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: disabled())
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: disabled())
    monkeypatch.setattr(requests, "put", lambda *args, **kwargs: disabled())
    monkeypatch.setattr(requests, "delete", lambda *args, **kwargs: disabled())


# @pytest.fixture(autouse=True)
# def mock_environment_for_config(monkeypatch):
#     monkeypatch.setenv('ENVIRONMENT', 'development')

# ----- CRUD ----- #


def test_read_one_task(client):
    response = client.get(ENDPOINT + '830')
    assert response.status_code == 200


def test_read_many_tasks(client):
    response = client.get(ENDPOINT)
    assert response.status_code == 200
    # assert len(response.json()) == 5


def test_create_task(client):
    print(TASKS_TO_CREATE[0])
    response = client.post(ENDPOINT, data=json.dumps(TASKS_TO_CREATE[0]))
    assert response.status_code == 200


def test_delete_task(client):
    tasks = client.get(ENDPOINT).json()
    task_to_delete = tasks[0]
    response = client.delete(f'{ENDPOINT}{task_to_delete["id"]}/')
    assert response.status_code == 204


# ----- EXTRA ENDPOINTS ----- #


def test_complete_task(client):
    response = client.post(ENDPOINT + 'complete/830/', data=TEST_TASK_IDS[0])
    assert response.status_code == 200


def test_read_completed_tasks(client):
    response = client.get(ENDPOINT + 'completed/')
    print(ENDPOINT + 'completed/')
    assert response.status_code == 200


def test_task_lifecycle(client):
    original_task = TASKS_TO_CREATE[1]
    created_task = client.post(ENDPOINT, data=json.dumps(original_task)).json()
    assert created_task['name'] == original_task['name']
    response_task = client.get(ENDPOINT + f'{created_task["id"]}').json()
    assert response_task['name'] == original_task['name']
    deleted_task = client.delete(ENDPOINT + f'{created_task["id"]}/').json()
    assert deleted_task['name'] == original_task['name']
    missing_task = client.get(ENDPOINT + f'{created_task["id"]}/')
    assert missing_task.status_code == 404
