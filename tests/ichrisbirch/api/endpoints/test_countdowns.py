from datetime import date

import pytest
from fastapi import status

from ichrisbirch import schemas
from tests.util import show_status_and_response
from tests.utils.database import insert_test_data_transactional

from .crud_test import ApiCrudTester

ENDPOINT = '/countdowns/'
NEW_OBJ = schemas.CountdownCreate(
    name='Countdown 4 Computer with notes priority 3',
    notes='Notes Countdown 4',
    due_date=date(2040, 1, 20),
)


@pytest.fixture
def countdown_crud_tester(txn_api_logged_in):
    """Provide ApiCrudTester with transactional test data."""
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'countdowns')
    crud_tester = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ)
    return client, crud_tester


def test_read_one(countdown_crud_tester):
    client, crud_tester = countdown_crud_tester
    crud_tester.test_read_one(client)


def test_read_many(countdown_crud_tester):
    client, crud_tester = countdown_crud_tester
    crud_tester.test_read_many(client)


def test_create(countdown_crud_tester):
    client, crud_tester = countdown_crud_tester
    crud_tester.test_create(client)


def test_delete(countdown_crud_tester):
    client, crud_tester = countdown_crud_tester
    crud_tester.test_delete(client)


def test_lifecycle(countdown_crud_tester):
    client, crud_tester = countdown_crud_tester
    crud_tester.test_lifecycle(client)


def test_partial_update(countdown_crud_tester):
    """Test partial update with only some fields."""
    client, crud_tester = countdown_crud_tester
    first_id = crud_tester.item_id_by_position(client, position=1)

    # Get original countdown
    original = client.get(f'{ENDPOINT}{first_id}/').json()

    # Update only notes
    response = client.patch(f'{ENDPOINT}{first_id}/', json={'notes': 'Updated notes'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    updated = response.json()
    assert updated['notes'] == 'Updated notes'
    assert updated['name'] == original['name']  # Other fields unchanged


class TestCountdownsNotFound:
    """Test 404 responses for non-existent countdowns."""

    def test_read_one_not_found(self, countdown_crud_tester):
        """GET /{id}/ returns 404 for non-existent countdown."""
        client, _ = countdown_crud_tester
        response = client.get(f'{ENDPOINT}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_delete_not_found(self, countdown_crud_tester):
        """DELETE /{id}/ returns 404 for non-existent countdown."""
        client, _ = countdown_crud_tester
        response = client.delete(f'{ENDPOINT}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_update_not_found(self, countdown_crud_tester):
        """PATCH /{id}/ returns 404 for non-existent countdown."""
        client, _ = countdown_crud_tester
        response = client.patch(f'{ENDPOINT}99999/', json={'name': 'Does Not Exist'})
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)
