import random
import pytest

from backend.common.db.sqlalchemy.base_class import Base
from backend.common.models.tasks import Task

SEED = 777
ENDPOINT = '/tasks/'
ENDPOINT_URL = 'http://localhost:8000' + ENDPOINT
FAKE_TASKS_TO_CREATE = 1000
NUM_TEST_TASKS = 5
TEST_TASK_IDS = random.choices(list(range(1, FAKE_TASKS_TO_CREATE + 1)), k=NUM_TEST_TASKS)


@pytest.fixture(scope="session", autouse=True)
def test_tasks(num: int = 1000) -> list[dict]:
    return [
        {
            "name": f"task-{num:03}",
            "category": f"category-{num:03}",
            "priority": random.randint(1, 100),
        }
        for num in range(num)
    ]


# @pytest.fixture(autouse=True)
# def disable_network_calls(monkeypatch):
#     def disabled():
#         raise RuntimeError("Network access not allowed during testing!")

#     monkeypatch.setattr(requests, "get", lambda *args, **kwargs: disabled())
#     monkeypatch.setattr(requests, "post", lambda *args, **kwargs: disabled())
#     monkeypatch.setattr(requests, "put", lambda *args, **kwargs: disabled())
#     monkeypatch.setattr(requests, "delete", lambda *args, **kwargs: disabled())


# @pytest.fixture(autouse=True)
# def mock_environment_for_config(monkeypatch):
#     monkeypatch.setenv('ENVIRONMENT', 'development')


# ----- CRUD ----- #


@pytest.mark.parametrize('task_id', list(TEST_TASK_IDS))
def test_read_one_task(task_id, client):
    response = client.get(ENDPOINT + str(task_id))
    assert response.status_code == 200


def test_read_many_tasks(client):
    response = client.get(ENDPOINT)
    assert response.status_code == 200
    assert len(response.json()) == 1000


# def test_create_task(client):
#     print(TASKS_TO_CREATE[0])
#     response = client.post(ENDPOINT, data=json.dumps(TASKS_TO_CREATE[0]))
#     assert response.status_code == 200


@pytest.mark.parametrize('task_id', list(TEST_TASK_IDS))
def test_delete_task(task_id, client):
    tasks = client.get(ENDPOINT).json()
    response = client.delete(f'{ENDPOINT}{task_id}/')
    assert response.status_code == 204


# # ----- EXTRA ENDPOINTS ----- #


# @pytest.mark.parametrize('task_id', list(TEST_TASK_IDS))
# def test_complete_task(task_id, client):
#     response = client.post(ENDPOINT + f'complete/{task_id}/')
#     assert response.status_code == 200


# def test_read_completed_tasks(client):
#     response = client.get(ENDPOINT + 'completed/')
#     print(ENDPOINT + 'completed/')
#     assert response.status_code == 200


# def test_task_lifecycle(client):
#     original_task = TASKS_TO_CREATE[1]
#     created_task = client.post(ENDPOINT, data=json.dumps(original_task)).json()
#     assert created_task['name'] == original_task['name']
#     response_task = client.get(ENDPOINT + f'{created_task["id"]}').json()
#     assert response_task['name'] == original_task['name']
#     deleted_task = client.delete(ENDPOINT + f'{created_task["id"]}/').json()
#     assert deleted_task['name'] == original_task['name']
#     missing_task = client.get(ENDPOINT + f'{created_task["id"]}/')
#     assert missing_task.status_code == 404
