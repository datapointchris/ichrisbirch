import logging

import pytest
from fastapi import status

from ichrisbirch import schemas
from ichrisbirch.models.autotask import AUTOTASK_FREQUENCIES
from ichrisbirch.models.task import TASK_CATEGORIES
from tests.util import show_status_and_response
from tests.utils.database import insert_test_data_transactional

from .crud_test import ApiCrudTester

logger = logging.getLogger(__name__)

NEW_OBJ = schemas.AutoTaskCreate(
    name='AutoTask 4 Computer with notes window 3',
    notes='Notes task 4',
    category='Computer',
    window_days=3,
    frequency='Biweekly',
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


@pytest.mark.parametrize('category', TASK_CATEGORIES)
def test_task_categories(txn_api_logged_in, category):
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'autotasks')
    test_obj = schemas.AutoTaskCreate(
        name='AutoTask 4 Computer with notes window 3',
        notes='Notes task 4',
        category=category,
        window_days=3,
        frequency='Biweekly',
    )
    created = client.post(ENDPOINT, json=test_obj.model_dump(mode='json'))
    assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)
    assert created.json()['name'] == test_obj.name


@pytest.mark.parametrize('frequency', AUTOTASK_FREQUENCIES)
def test_task_frequencies(txn_api_logged_in, frequency):
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'autotasks')
    test_obj = schemas.AutoTaskCreate(
        name='AutoTask 4 Computer with notes window 3',
        notes='Notes task 4',
        category='Personal',
        window_days=3,
        frequency=frequency,
    )
    created = client.post(ENDPOINT, json=test_obj.model_dump(mode='json'))
    assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)
    assert created.json()['name'] == test_obj.name


def test_update_autotask(autotask_crud_tester):
    """Test updating an AutoTask's fields via PATCH."""
    client, crud_tester = autotask_crud_tester
    first_id = crud_tester.item_id_by_position(client, position=1)

    response = client.patch(f'{ENDPOINT}{first_id}/', json={'name': 'Updated Name', 'window_days': 9, 'anchor': 'calendar'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)

    updated = response.json()
    assert updated['name'] == 'Updated Name'
    assert updated['window_days'] == 9
    assert updated['anchor'] == 'calendar'


def test_clearing_the_window_falls_back_to_the_category(autotask_crud_tester):
    client, crud_tester = autotask_crud_tester
    first_id = crud_tester.item_id_by_position(client, position=1)

    response = client.patch(f'{ENDPOINT}{first_id}/', json={'window_days': None})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert response.json()['window_days'] is None


def test_a_new_autotask_is_completion_anchored(txn_api_logged_in):
    client, _ = txn_api_logged_in
    created = client.post(ENDPOINT, json={'name': 'Trim nails', 'category': 'Dingo', 'frequency': 'Biweekly'})
    assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)
    assert created.json()['anchor'] == 'completion'
    assert created.json()['window_days'] is None


@pytest.mark.parametrize('method', ['post', 'patch'])
def test_an_unknown_anchor_names_the_known_ones(autotask_crud_tester, method):
    client, crud_tester = autotask_crud_tester
    if method == 'post':
        response = client.post(ENDPOINT, json={**NEW_OBJ.model_dump(mode='json'), 'anchor': 'weekly'})
    else:
        first_id = crud_tester.item_id_by_position(client, position=1)
        response = client.patch(f'{ENDPOINT}{first_id}/', json={'anchor': 'weekly'})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)
    assert 'completion' in response.json()['detail']


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

    tasks_response = client.get('/tasks/')
    assert tasks_response.status_code == status.HTTP_200_OK
    [copy] = [task for task in tasks_response.json() if task['name'] == autotask_before['name']]
    assert copy['autotask_id'] == first_id
    assert copy['window_days'] == autotask_before['window_days']


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

    def test_update_not_found(self, autotask_crud_tester):
        """PATCH /{id}/ returns 404 for non-existent autotask."""
        client, _ = autotask_crud_tester
        response = client.patch(f'{ENDPOINT}99999/', json={'name': 'Nope'})
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_run_not_found(self, autotask_crud_tester):
        """PATCH /{id}/run/ returns 404 for non-existent autotask."""
        client, _ = autotask_crud_tester
        response = client.patch(f'{ENDPOINT}99999/run/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)
