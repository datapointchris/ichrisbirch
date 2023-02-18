import json

import pytest

from ichrisbirch import models
from ichrisbirch.api.endpoints import tasks
from tests.data_generators import TaskDataGenerator
from tests.helpers import format_endpoint

ENDPOINT = 'tasks'
SEED = 777
NUM_RECORDS_TO_GENERATE = 100
NUM_TEST_RECORDS = 10

task_data_gen = TaskDataGenerator(NUM_RECORDS_TO_GENERATE, NUM_TEST_RECORDS, SEED)


@pytest.fixture(scope='function')
def test_data() -> list[dict]:
    """Returns generated test data"""
    return task_data_gen.generated_data


@pytest.fixture(scope='module')
def data_model():
    """Returns the SQLAlchemy model to use for the data"""
    return models.Task


@pytest.fixture(scope='module')
def router():
    """Returns the API router to use for this test module"""
    return tasks.router


@pytest.mark.parametrize('task_id', task_data_gen.random_ids)
def test_read_one_task(postgres_testdb_in_docker, insert_test_data, test_app, task_id):
    """Test if able to read one task using the endpoint"""
    response = test_app.get(format_endpoint([ENDPOINT, task_id]))
    assert response.status_code == 200


def test_read_many_tasks(postgres_testdb_in_docker, insert_test_data, test_app):
    """Test if able to read many tasks using the endpoint"""
    response = test_app.get(format_endpoint(ENDPOINT))
    assert response.status_code == 200
    assert len(response.json()) == NUM_RECORDS_TO_GENERATE


@pytest.mark.parametrize('test_task', task_data_gen.random_records)
def test_create_task(postgres_testdb_in_docker, insert_test_data, test_app, test_task):
    """Test if able to create a task using the endpoint"""
    response = test_app.post(format_endpoint(ENDPOINT), data=json.dumps(test_task))
    assert response.status_code == 200


@pytest.mark.parametrize('task_id', task_data_gen.random_ids)
def test_delete_task(postgres_testdb_in_docker, insert_test_data, test_app, task_id):
    """Test if able to delete a task using the endpoint"""
    endp = format_endpoint([ENDPOINT, task_id])
    task = test_app.get(endp)
    response = test_app.delete(endp)
    deleted = test_app.get(endp)
    assert response.status_code == 200
    assert response.json() == task.json()
    assert deleted.status_code == 404


@pytest.mark.parametrize('task_id', task_data_gen.random_ids)
def test_complete_task(postgres_testdb_in_docker, insert_test_data, test_app, task_id):
    """Test if able to complete a task using the endpoint"""
    response = test_app.post(format_endpoint([ENDPOINT, 'complete', task_id]))
    assert response.status_code == 200


@pytest.mark.parametrize('task_id', task_data_gen.random_ids)
def test_read_completed_tasks(postgres_testdb_in_docker, insert_test_data, test_app, task_id):
    """Test if able to read completed tasks using the endpoint"""
    test_app.post(format_endpoint([ENDPOINT, 'complete', task_id]))
    response = test_app.get(format_endpoint([ENDPOINT, 'completed']))
    print(response.json())
    assert response.status_code == 200


@pytest.mark.parametrize('test_task', task_data_gen.random_records)
def test_task_lifecycle(postgres_testdb_in_docker, insert_test_data, test_app, test_task):
    """Integration test for CRUD lifecylce of a task"""
    created_task = test_app.post(format_endpoint(ENDPOINT), data=json.dumps(test_task)).json()
    task_id = created_task.get('id')
    endp = format_endpoint([ENDPOINT, task_id])
    response_task = test_app.get(endp).json()
    deleted_task = test_app.delete(endp).json()
    missing_task = test_app.get(endp)
    assert created_task['name'] == test_task['name']
    assert response_task['name'] == test_task['name']
    assert deleted_task['name'] == test_task['name']
    assert missing_task.status_code == 404
