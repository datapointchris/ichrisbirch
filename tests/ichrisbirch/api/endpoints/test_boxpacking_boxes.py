import pytest
from fastapi import status

from ichrisbirch import schemas
from ichrisbirch.models.box import BoxSize
from tests.util import show_status_and_response
from tests.utils.database import insert_test_data_transactional

from .crud_test import ApiCrudTester

NEW_OBJ = schemas.BoxCreate(
    name='Box 4 - Bag of clothes',
    number=4,
    size=BoxSize.Bag,
    essential=True,
    warm=False,
    liquid=False,
)
ENDPOINT = '/box-packing/boxes/'


@pytest.fixture
def box_crud_tester(txn_api_logged_in):
    """Provide ApiCrudTester with transactional test data."""
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'boxes')  # boxitems inserted via Box.items relationship
    crud_tester = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ)
    return client, crud_tester


def test_read_one(box_crud_tester):
    client, crud_tester = box_crud_tester
    crud_tester.test_read_one(client)


def test_read_many(box_crud_tester):
    client, crud_tester = box_crud_tester
    crud_tester.test_read_many(client)


def test_create(box_crud_tester):
    client, crud_tester = box_crud_tester
    crud_tester.test_create(client)


def test_delete(box_crud_tester):
    client, crud_tester = box_crud_tester
    crud_tester.test_delete(client)


def test_lifecycle(box_crud_tester):
    client, crud_tester = box_crud_tester
    crud_tester.test_lifecycle(client)


def test_search_box_items(box_crud_tester):
    client, _ = box_crud_tester
    search_term = 'find'
    search_results = client.get('/box-packing/search/', params={'q': search_term})
    assert search_results.status_code == status.HTTP_200_OK, show_status_and_response(search_results)
    assert len(search_results.json()) == 1

    search_term = 'home'
    search_results = client.get('/box-packing/search/', params={'q': search_term})
    assert search_results.status_code == status.HTTP_200_OK, show_status_and_response(search_results)
    assert len(search_results.json()) == 0


# must explicitly use values because Sixteen = '16x16x16', where '16x16x16' is not valid Enum member name
@pytest.mark.parametrize('box_size', list(BoxSize))
def test_create_box_all_sizes(txn_api_logged_in, box_size):
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'boxes')
    test_box = schemas.BoxCreate(
        name='Box X',
        number=5,
        size=box_size,
        essential=True,
        warm=False,
        liquid=False,
    )
    response = client.post(ENDPOINT, json=test_box.model_dump())
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    assert dict(response.json())['name'] == test_box.name


@pytest.mark.parametrize('essential', [True, False])
@pytest.mark.parametrize('warm', [True, False])
@pytest.mark.parametrize('liquid', [True, False])
def test_create_box_options_combinations(txn_api_logged_in, essential, warm, liquid):
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'boxes')
    test_box = schemas.BoxCreate(
        name='Box X',
        number=5,
        size=BoxSize.Large,
        essential=essential,
        warm=warm,
        liquid=liquid,
    )
    response = client.post(ENDPOINT, json=test_box.model_dump())
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    assert dict(response.json())['name'] == test_box.name
