import logging

import pytest
from fastapi import status

from ichrisbirch import schemas
from ichrisbirch.models.autotask import AutoTaskFrequency
from ichrisbirch.models.task import TaskCategory
from tests.util import show_status_and_response
from tests.utils.database import insert_test_data_transactional

from .crud_test import ApiCrudTester

logger = logging.getLogger(__name__)

NEW_OBJ = schemas.AutoTaskCreate(
    name='AutoTask 4 Computer with notes priority 3',
    notes='Notes task 4',
    category=TaskCategory.Computer,
    priority=3,
    frequency=AutoTaskFrequency.Biweekly,
)

ENDPOINT = '/autotasks/'


@pytest.fixture
def autotask_crud_tester(txn_api_logged_in):
    """Provide ApiCrudTester with transactional test data."""
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'autotasks')
    crud_tester = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ)
    return client, crud_tester


def test_read_one(autotask_crud_tester):
    client, crud_tester = autotask_crud_tester
    crud_tester.test_read_one(client)


def test_read_many(autotask_crud_tester):
    client, crud_tester = autotask_crud_tester
    crud_tester.test_read_many(client)


def test_create(autotask_crud_tester):
    client, crud_tester = autotask_crud_tester
    crud_tester.test_create(client)


def test_delete(autotask_crud_tester):
    client, crud_tester = autotask_crud_tester
    crud_tester.test_delete(client)


def test_lifecycle(autotask_crud_tester):
    client, crud_tester = autotask_crud_tester
    crud_tester.test_lifecycle(client)


@pytest.mark.parametrize('category', list(TaskCategory))
def test_task_categories(txn_api_logged_in, category):
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'autotasks')
    test_obj = schemas.AutoTaskCreate(
        name='AutoTask 4 Computer with notes priority 3',
        notes='Notes task 4',
        category=category,
        priority=3,
        frequency=AutoTaskFrequency.Biweekly,
    )
    created = client.post(ENDPOINT, json=test_obj.model_dump(mode='json'))
    assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)
    assert created.json()['name'] == test_obj.name


@pytest.mark.parametrize('frequency', list(AutoTaskFrequency))
def test_task_frequencies(txn_api_logged_in, frequency):
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'autotasks')
    test_obj = schemas.AutoTaskCreate(
        name='AutoTask 4 Computer with notes priority 3',
        notes='Notes task 4',
        category=TaskCategory.Personal,
        priority=3,
        frequency=frequency,
    )
    created = client.post(ENDPOINT, json=test_obj.model_dump(mode='json'))
    assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)
    assert created.json()['name'] == test_obj.name


def test_run_autotask(autotask_crud_tester):
    """Test running an AutoTask creates a Task and updates run count."""
    client, crud_tester = autotask_crud_tester
    first_id = crud_tester.item_id_by_position(client, position=1)

    # Get initial state
    autotask_before = client.get(f'{ENDPOINT}{first_id}/').json()
    initial_run_count = autotask_before['run_count']

    # Run the autotask
    response = client.patch(f'{ENDPOINT}{first_id}/run/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)

    # Verify run_count incremented
    autotask_after = response.json()
    assert autotask_after['run_count'] == initial_run_count + 1
    assert autotask_after['last_run_date'] is not None

    # Verify a task was created with matching name
    tasks_response = client.get('/tasks/')
    assert tasks_response.status_code == status.HTTP_200_OK
    tasks = tasks_response.json()
    assert any(task['name'] == autotask_before['name'] for task in tasks)


class TestAutoTasksNotFound:
    """Test 404 responses for non-existent autotasks."""

    def test_read_one_not_found(self, autotask_crud_tester):
        """GET /{id}/ returns 404 for non-existent autotask."""
        client, _ = autotask_crud_tester
        response = client.get(f'{ENDPOINT}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_delete_not_found(self, autotask_crud_tester):
        """DELETE /{id}/ returns 404 for non-existent autotask."""
        client, _ = autotask_crud_tester
        response = client.delete(f'{ENDPOINT}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_run_not_found(self, autotask_crud_tester):
        """PATCH /{id}/run/ returns 404 for non-existent autotask."""
        client, _ = autotask_crud_tester
        response = client.patch(f'{ENDPOINT}99999/run/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)
