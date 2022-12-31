import pytest
import json
from euphoria.tests.data_generators import TaskDataGenerator
from euphoria.tests.helpers import endpoint
from euphoria.backend.common.models.tasks import Task
from euphoria.backend.api.endpoints import tasks


ENDPOINT = 'tasks'
SEED = 777
NUMBER_OF_RECORDS_TO_GENERATE = 100
NUM_TEST_RECORDS = 10

fake_tasks = TaskDataGenerator(SEED)
fake_tasks.generate(NUMBER_OF_RECORDS_TO_GENERATE)
RANDOM_IDS = fake_tasks.random_ids(NUM_TEST_RECORDS)
RANDOM_RECORDS = fake_tasks.random_records(NUM_TEST_RECORDS)


@pytest.fixture(scope='function')
def test_data() -> list[dict]:
    # fake_tasks.generate(NUMBER_OF_RECORDS_TO_GENERATE)
    return fake_tasks.generated_data


@pytest.fixture(scope='module')
def data_model() -> Task:
    return Task


@pytest.fixture(scope='module')
def router():
    return tasks.router


@pytest.mark.parametrize('task_id', RANDOM_IDS)
def test_read_one_task(postgres_testdb_in_docker, insert_test_data, test_app, task_id):
    response = test_app.get(endpoint([ENDPOINT, task_id]))
    assert response.status_code == 200


def test_read_many_tasks(postgres_testdb_in_docker, insert_test_data, test_app):
    response = test_app.get(endpoint(ENDPOINT))
    assert response.status_code == 200
    assert len(response.json()) == NUMBER_OF_RECORDS_TO_GENERATE


@pytest.mark.parametrize('test_task', RANDOM_RECORDS)
def test_create_task(postgres_testdb_in_docker, insert_test_data, test_app, test_task):
    response = test_app.post(endpoint(ENDPOINT), data=json.dumps(test_task))
    assert response.status_code == 200


@pytest.mark.parametrize('task_id', RANDOM_IDS)
def test_delete_task(postgres_testdb_in_docker, insert_test_data, test_app, task_id):
    endp = endpoint([ENDPOINT, task_id])
    task = test_app.get(endp)
    response = test_app.delete(endp)
    deleted = test_app.get(endp)
    assert response.status_code == 200
    assert response.json() == task.json()
    assert deleted.status_code == 404


@pytest.mark.parametrize('task_id', RANDOM_IDS)
def test_complete_task(postgres_testdb_in_docker, insert_test_data, test_app, task_id):
    response = test_app.post(endpoint([ENDPOINT, 'complete', task_id]))
    assert response.status_code == 200


@pytest.mark.parametrize('task_id', RANDOM_IDS)
def test_read_completed_tasks(postgres_testdb_in_docker, insert_test_data, test_app, task_id):
    test_app.post(endpoint([ENDPOINT, 'complete', task_id]))
    response = test_app.get(endpoint([ENDPOINT, 'completed']))
    print(response.json())
    assert response.status_code == 200


@pytest.mark.parametrize('test_task', RANDOM_RECORDS)
def test_task_lifecycle(postgres_testdb_in_docker, insert_test_data, test_app, test_task):
    created_task = test_app.post(endpoint(ENDPOINT), data=json.dumps(test_task)).json()
    task_id = created_task.get('id')
    endp = endpoint([ENDPOINT, task_id])
    response_task = test_app.get(endp).json()
    deleted_task = test_app.delete(endp).json()
    missing_task = test_app.get(endp)
    assert created_task['name'] == test_task['name']
    assert response_task['name'] == test_task['name']
    assert deleted_task['name'] == test_task['name']
    assert missing_task.status_code == 404
