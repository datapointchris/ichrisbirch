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


def test_read_many_boxes_with_limit(box_crud_tester):
    """Test limit parameter on GET /boxes/."""
    client, _ = box_crud_tester
    # Get all boxes first
    all_boxes = client.get(ENDPOINT)
    assert all_boxes.status_code == status.HTTP_200_OK
    total = len(all_boxes.json())
    assert total >= 2, 'Need at least 2 boxes for limit test'

    # Test with limit=1
    response = client.get(ENDPOINT, params={'limit': 1})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 1


def test_partial_update_box(box_crud_tester):
    """Test partial update preserves other fields."""
    client, crud_tester = box_crud_tester
    first_id = crud_tester.item_id_by_position(client, position=1)

    original = client.get(f'{ENDPOINT}{first_id}/').json()
    response = client.patch(f'{ENDPOINT}{first_id}/', json={'name': 'Updated Box Name'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    updated = response.json()
    assert updated['name'] == 'Updated Box Name'
    assert updated['number'] == original['number']


class TestBoxesNotFound:
    """Test 404 responses for non-existent boxes."""

    def test_read_one_not_found(self, box_crud_tester):
        """GET /boxes/{id}/ returns 404 for non-existent box."""
        client, _ = box_crud_tester
        response = client.get(f'{ENDPOINT}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_delete_not_found(self, box_crud_tester):
        """DELETE /boxes/{id}/ returns 404 for non-existent box."""
        client, _ = box_crud_tester
        response = client.delete(f'{ENDPOINT}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_update_not_found(self, box_crud_tester):
        """PATCH /boxes/{id}/ returns 404 for non-existent box."""
        client, _ = box_crud_tester
        response = client.patch(f'{ENDPOINT}99999/', json={'name': 'Does Not Exist'})
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)
