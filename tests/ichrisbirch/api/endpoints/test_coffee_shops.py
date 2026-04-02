import pytest
from fastapi import status

from ichrisbirch import schemas
from tests.util import show_status_and_response
from tests.utils.database import insert_test_data_transactional

from .crud_test import ApiCrudTester

ENDPOINT = '/coffee/shops/'
NEW_OBJ = schemas.CoffeeShopCreate(
    name='Four Barrel Coffee',
    city='San Francisco',
    state='CA',
    country='USA',
    rating=3.8,
    notes='Charming industrial space',
)


@pytest.fixture
def shop_crud_tester(txn_api_logged_in):
    """Provide ApiCrudTester with transactional test data."""
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'coffee_shops')
    crud_tester = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ, verify_attr='name')
    return client, crud_tester


def test_read_one(shop_crud_tester):
    client, crud_tester = shop_crud_tester
    crud_tester.test_read_one(client)


def test_read_many(shop_crud_tester):
    client, crud_tester = shop_crud_tester
    crud_tester.test_read_many(client)


def test_create(shop_crud_tester):
    client, crud_tester = shop_crud_tester
    crud_tester.test_create(client)


def test_delete(shop_crud_tester):
    client, crud_tester = shop_crud_tester
    crud_tester.test_delete(client)


def test_lifecycle(shop_crud_tester):
    client, crud_tester = shop_crud_tester
    crud_tester.test_lifecycle(client)


def test_update_shop(shop_crud_tester):
    client, crud_tester = shop_crud_tester
    shop_id = crud_tester.item_id_by_position(client, position=1)
    original = client.get(f'{ENDPOINT}{shop_id}/').json()

    # Update rating and review
    response = client.patch(f'{ENDPOINT}{shop_id}/', json={'rating': 4.9, 'review': 'Outstanding espresso program.'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    data = response.json()
    assert data['rating'] == 4.9
    assert data['review'] == 'Outstanding espresso program.'
    assert data['name'] == original['name'], 'Untouched fields should not change'

    # Update location fields
    response = client.patch(f'{ENDPOINT}{shop_id}/', json={'city': 'Berkeley', 'state': 'CA'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    data = response.json()
    assert data['city'] == 'Berkeley'
    assert data['rating'] == 4.9, 'Previous update should persist'


def test_filter_shops_by_city(shop_crud_tester):
    client, _ = shop_crud_tester
    response = client.get(ENDPOINT, params={'city': 'San Francisco'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    results = response.json()
    assert all('san francisco' in (s['city'] or '').lower() for s in results)


def test_filter_shops_by_city_no_results(shop_crud_tester):
    client, _ = shop_crud_tester
    response = client.get(ENDPOINT, params={'city': 'NowhereLand99'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 0


class TestCoffeeShopsNotFound:
    def test_read_one_not_found(self, shop_crud_tester):
        client, _ = shop_crud_tester
        response = client.get(f'{ENDPOINT}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_update_not_found(self, shop_crud_tester):
        client, _ = shop_crud_tester
        response = client.patch(f'{ENDPOINT}99999/', json={'name': 'Ghost Shop'})
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_delete_not_found(self, shop_crud_tester):
        client, _ = shop_crud_tester
        response = client.delete(f'{ENDPOINT}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)
