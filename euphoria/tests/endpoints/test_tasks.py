import pytest
import json
from ..data_generators import TaskDataGenerator
from ..helpers import endpoint
from ..test_config import test_config

ENDPOINT = 'tasks'
task_faker = TaskDataGenerator(ENDPOINT, test_config.SEED)
fake_tasks = task_faker.generate(test_config.NUM_FAKE)


@pytest.fixture(autouse=True)
def test_data() -> list[dict]:
    return fake_tasks


@pytest.mark.parametrize('task_id', task_faker.ids_from_generated(test_config.NUM_TEST))
def test_read_one_task(task_id, client):
    response = client.get(endpoint(ENDPOINT, task_id))
    assert response.status_code == 200


def test_read_many_tasks(client):
    response = client.get(endpoint(ENDPOINT))
    assert response.status_code == 200
    assert len(response.json()) == 1000


@pytest.mark.parametrize('test_task', task_faker.records_from_generated(test_config.NUM_TEST))
def test_create_task(test_task, client):
    response = client.post(endpoint(ENDPOINT), data=json.dumps(test_task))
    assert response.status_code == 200


@pytest.mark.parametrize('task_id', task_faker.ids_from_generated(test_config.NUM_TEST))
def test_delete_task(task_id, client):
    task = client.get(endpoint(ENDPOINT, task_id))
    response = client.delete(endpoint(ENDPOINT, task_id))
    deleted = client.get(endpoint(ENDPOINT, task_id))
    assert response.status_code == 200
    assert response.json() == task.json()
    assert deleted.status_code == 404


@pytest.mark.parametrize('task_id', task_faker.ids_from_generated(test_config.NUM_TEST))
def test_complete_task(task_id, client):
    response = client.post(endpoint(ENDPOINT, 'complete', task_id))
    assert response.status_code == 200


@pytest.mark.parametrize('task_id', task_faker.ids_from_generated(test_config.NUM_TEST))
def test_read_completed_tasks(task_id, client):
    client.post(endpoint(ENDPOINT, 'complete', task_id))
    response = client.get(endpoint(ENDPOINT, 'completed'))
    print(response.json())
    assert response.status_code == 200


@pytest.mark.parametrize('test_task', task_faker.records_from_generated(test_config.NUM_TEST))
def test_task_lifecycle(test_task, client):
    created_task = client.post(endpoint(ENDPOINT), data=json.dumps(test_task)).json()
    task_id = created_task.get('id')
    response_task = client.get(endpoint(ENDPOINT, task_id)).json()
    deleted_task = client.delete(endpoint(ENDPOINT, task_id)).json()
    missing_task = client.get(endpoint(ENDPOINT, task_id))
    assert created_task['name'] == test_task['name']
    assert response_task['name'] == test_task['name']
    assert deleted_task['name'] == test_task['name']
    assert missing_task.status_code == 404
