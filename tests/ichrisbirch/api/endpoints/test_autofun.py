import logging

import pytest
from fastapi import status

from ichrisbirch import schemas
from tests.util import show_status_and_response
from tests.utils.database import insert_test_data_transactional

from .crud_test import ApiCrudTester

logger = logging.getLogger(__name__)

NEW_OBJ = schemas.AutoFunCreate(
    name='Try the new ramen place downtown',
    notes='Opens at 11am, cash only',
)

ENDPOINT = '/autofun/'


@pytest.fixture
def autofun_crud_tester(txn_api_logged_in):
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'autofun')
    crud_tester = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ)
    return client, crud_tester


def test_read_one(autofun_crud_tester):
    client, crud_tester = autofun_crud_tester
    crud_tester.test_read_one(client)


def test_read_many(autofun_crud_tester):
    client, crud_tester = autofun_crud_tester
    crud_tester.test_read_many(client)


def test_create(autofun_crud_tester):
    client, crud_tester = autofun_crud_tester
    crud_tester.test_create(client)


def test_delete(autofun_crud_tester):
    client, crud_tester = autofun_crud_tester
    crud_tester.test_delete(client)


def test_lifecycle(autofun_crud_tester):
    client, crud_tester = autofun_crud_tester
    crud_tester.test_lifecycle(client)


def test_create_without_notes(txn_api_logged_in):
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'autofun')
    obj = schemas.AutoFunCreate(name='Bike across the Golden Gate Bridge')
    response = client.post(ENDPOINT, json=obj.model_dump(mode='json'))
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    assert response.json()['notes'] is None
    assert response.json()['is_completed'] is False


def test_read_many_filter_completed(autofun_crud_tester):
    """GET /?completed=false returns only active items."""
    client, _ = autofun_crud_tester
    response = client.get(f'{ENDPOINT}?completed=false')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert all(not item['is_completed'] for item in response.json())


def test_update_autofun(autofun_crud_tester):
    client, crud_tester = autofun_crud_tester
    first_id = crud_tester.item_id_by_position(client, position=1)
    response = client.patch(f'{ENDPOINT}{first_id}/', json={'name': 'Updated name', 'notes': 'Updated notes'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert response.json()['name'] == 'Updated name'
    assert response.json()['notes'] == 'Updated notes'


class TestAutoFunNotFound:
    def test_read_one_not_found(self, autofun_crud_tester):
        client, _ = autofun_crud_tester
        response = client.get(f'{ENDPOINT}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_delete_not_found(self, autofun_crud_tester):
        client, _ = autofun_crud_tester
        response = client.delete(f'{ENDPOINT}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_update_not_found(self, autofun_crud_tester):
        client, _ = autofun_crud_tester
        response = client.patch(f'{ENDPOINT}99999/', json={'name': 'Nope'})
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)
