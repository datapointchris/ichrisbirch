import pytest
from fastapi import status

from ichrisbirch import schemas
from tests.util import show_status_and_response
from tests.utils.database import insert_test_data_transactional

from .crud_test import ApiCrudTester

SHOPS_ENDPOINT = '/coffee/shops/'
BEANS_ENDPOINT = '/coffee/beans/'
NEW_OBJ = schemas.CoffeeBeanCreate(
    name='Guatemala Antigua',
    roaster='Counter Culture',
    origin='Guatemala',
    process='washed',
    roast_level='medium',
    brew_method='aeropress',
    flavor_notes='brown sugar, almond, citrus',
    rating=4.1,
    price=15.50,
)


@pytest.fixture
def bean_crud_tester(txn_api_logged_in):
    """Provide ApiCrudTester with transactional test data.

    Shops must be inserted first to satisfy the FK constraint in coffee_beans.
    """
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'coffee_shops')
    insert_test_data_transactional(session, 'coffee_beans')
    crud_tester = ApiCrudTester(endpoint=BEANS_ENDPOINT, new_obj=NEW_OBJ, verify_attr='name')
    return client, crud_tester


def test_read_one(bean_crud_tester):
    client, crud_tester = bean_crud_tester
    crud_tester.test_read_one(client)


def test_read_many(bean_crud_tester):
    client, crud_tester = bean_crud_tester
    crud_tester.test_read_many(client)


def test_create(bean_crud_tester):
    client, crud_tester = bean_crud_tester
    crud_tester.test_create(client)


def test_delete(bean_crud_tester):
    client, crud_tester = bean_crud_tester
    crud_tester.test_delete(client)


def test_lifecycle(bean_crud_tester):
    client, crud_tester = bean_crud_tester
    crud_tester.test_lifecycle(client)


def test_create_bean_with_purchase_source_only(bean_crud_tester):
    """Beans can be linked to a free-text source instead of a shop FK."""
    client, _ = bean_crud_tester
    response = client.post(
        BEANS_ENDPOINT,
        json={
            'name': 'Trade Subscription Blend',
            'roaster': 'Trade Coffee',
            'origin': 'Colombia',
            'purchase_source': 'Trade Coffee monthly subscription',
        },
    )
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    data = response.json()
    assert data['purchase_source'] == 'Trade Coffee monthly subscription'
    assert data['coffee_shop_id'] is None


def test_create_bean_without_any_source(bean_crud_tester):
    """Beans with neither shop nor source are allowed — both fields are nullable."""
    client, _ = bean_crud_tester
    response = client.post(BEANS_ENDPOINT, json={'name': 'Mystery Blend', 'roaster': 'Unknown'})
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    data = response.json()
    assert data['coffee_shop_id'] is None
    assert data['purchase_source'] is None


def test_update_bean_fields(bean_crud_tester):
    client, crud_tester = bean_crud_tester
    bean_id = crud_tester.item_id_by_position(client, position=1)
    original = client.get(f'{BEANS_ENDPOINT}{bean_id}/').json()

    response = client.patch(f'{BEANS_ENDPOINT}{bean_id}/', json={'rating': 4.9, 'review': 'Exceptional.'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    data = response.json()
    assert data['rating'] == 4.9
    assert data['review'] == 'Exceptional.'
    assert data['name'] == original['name'], 'Untouched fields should not change'


def test_update_bean_nulls_coffee_shop_id(bean_crud_tester):
    """Should be able to detach a bean from a shop (set FK to null)."""
    client, crud_tester = bean_crud_tester
    # Create a bean with a shop ID
    shops = client.get(SHOPS_ENDPOINT).json()
    assert len(shops) > 0
    shop_id = shops[0]['id']

    bean_resp = client.post(
        BEANS_ENDPOINT,
        json={'name': 'FK Test Bean', 'roaster': 'Test Roaster', 'coffee_shop_id': shop_id},
    )
    assert bean_resp.status_code == status.HTTP_201_CREATED, show_status_and_response(bean_resp)
    bean_id = bean_resp.json()['id']
    assert bean_resp.json()['coffee_shop_id'] == shop_id

    # Detach from shop, add purchase_source
    response = client.patch(
        f'{BEANS_ENDPOINT}{bean_id}/',
        json={'coffee_shop_id': None, 'purchase_source': 'Online store'},
    )
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    data = response.json()
    assert data['coffee_shop_id'] is None
    assert data['purchase_source'] == 'Online store'


def test_filter_beans_by_roast_level(bean_crud_tester):
    client, _ = bean_crud_tester
    response = client.get(BEANS_ENDPOINT, params={'roast_level': 'light'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    results = response.json()
    assert all(b['roast_level'] == 'light' for b in results)


def test_filter_beans_by_brew_method(bean_crud_tester):
    client, _ = bean_crud_tester
    response = client.get(BEANS_ENDPOINT, params={'brew_method': 'pour-over'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    results = response.json()
    assert all(b['brew_method'] == 'pour-over' for b in results)


def test_filter_beans_no_results(bean_crud_tester):
    client, _ = bean_crud_tester
    response = client.get(BEANS_ENDPOINT, params={'roast_level': 'dark'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 0


class TestCoffeeBeansNotFound:
    def test_read_one_not_found(self, bean_crud_tester):
        client, _ = bean_crud_tester
        response = client.get(f'{BEANS_ENDPOINT}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_update_not_found(self, bean_crud_tester):
        client, _ = bean_crud_tester
        response = client.patch(f'{BEANS_ENDPOINT}99999/', json={'name': 'Ghost Bean'})
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_delete_not_found(self, bean_crud_tester):
        client, _ = bean_crud_tester
        response = client.delete(f'{BEANS_ENDPOINT}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)
