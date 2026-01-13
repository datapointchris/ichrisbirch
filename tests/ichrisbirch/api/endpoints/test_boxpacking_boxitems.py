import pytest
from fastapi import status

from ichrisbirch import schemas
from tests.util import show_status_and_response
from tests.utils.database import insert_test_data_transactional

from .crud_test import ApiCrudTester

ENDPOINT = '/box-packing/items/'


def get_empty_box(test_api_client):
    """Find a box with no items (essential=False indicates empty box in test data)."""
    boxes = test_api_client.get('/box-packing/boxes/')
    for box in boxes.json():
        if not box['essential']:
            return box
    raise ValueError('No empty box found in test data')


def get_box_with_liquid_item(test_api_client):
    """Find a box that has liquid=True (has a liquid item)."""
    boxes = test_api_client.get('/box-packing/boxes/')
    for box in boxes.json():
        if box['liquid']:
            return box
    raise ValueError('No box with liquid item found in test data')


def create_crud_tester(box_id: int):
    """Create ApiCrudTester with dynamic box_id."""
    new_obj = schemas.BoxItemCreate(
        box_id=box_id,
        name='Pants',
        essential=True,
        warm=False,
        liquid=False,
    )
    return ApiCrudTester(endpoint=ENDPOINT, new_obj=new_obj)


@pytest.fixture
def boxitem_test_data(txn_api_logged_in):
    """Provide transactional test data for box item tests."""
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'boxes')  # boxitems inserted via Box.items relationship
    return client


def test_read_one(boxitem_test_data):
    client = boxitem_test_data
    boxes = client.get('/box-packing/boxes/')
    first_box_id = boxes.json()[0]['id']
    crud_tester = create_crud_tester(first_box_id)
    crud_tester.test_read_one(client)


def test_read_many(boxitem_test_data):
    client = boxitem_test_data
    boxes = client.get('/box-packing/boxes/')
    first_box_id = boxes.json()[0]['id']
    crud_tester = create_crud_tester(first_box_id)
    crud_tester.test_read_many(client)


def test_create(boxitem_test_data):
    """Adding an essential item to an empty box should update the box essential detail to True."""
    client = boxitem_test_data
    empty_box = get_empty_box(client)
    box_id = empty_box['id']

    box = schemas.Box(**client.get(f'/box-packing/boxes/{box_id}/').json())
    assert not box.essential

    crud_tester = create_crud_tester(box_id)
    crud_tester.test_create(client)

    box = schemas.Box(**client.get(f'/box-packing/boxes/{box_id}/').json())
    assert box.essential


def test_delete(boxitem_test_data):
    """Deleting the liquid item from a box should update the box liquid detail to False."""
    client = boxitem_test_data
    liquid_box = get_box_with_liquid_item(client)
    box_id = liquid_box['id']

    box = schemas.Box(**client.get(f'/box-packing/boxes/{box_id}/').json())
    assert box.liquid

    crud_tester = create_crud_tester(box_id)
    crud_tester.test_delete(client)

    box = schemas.Box(**client.get(f'/box-packing/boxes/{box_id}/').json())
    assert not box.liquid


def test_lifecycle(boxitem_test_data):
    client = boxitem_test_data
    boxes = client.get('/box-packing/boxes/')
    first_box_id = boxes.json()[0]['id']
    crud_tester = create_crud_tester(first_box_id)
    crud_tester.test_lifecycle(client)


def test_read_many_items_with_limit(boxitem_test_data):
    """Test limit parameter on GET /items/."""
    client = boxitem_test_data
    # Get all items first
    all_items = client.get(ENDPOINT)
    assert all_items.status_code == status.HTTP_200_OK
    total = len(all_items.json())
    assert total >= 2, 'Need at least 2 items for limit test'

    # Test with limit=1
    response = client.get(ENDPOINT, params={'limit': 1})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 1


def test_read_orphan_items(boxitem_test_data):
    """Test GET /items/orphans/ returns items without a box."""
    client = boxitem_test_data
    # Get an item and remove it from its box
    items = client.get(ENDPOINT).json()
    first_item = items[0]
    item_id = first_item['id']

    # Update item to have no box (orphan it) - BoxItemUpdate requires id in body
    response = client.patch(f'{ENDPOINT}{item_id}/', json={'id': item_id, 'box_id': None})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)

    # Check orphans endpoint
    orphans = client.get(f'{ENDPOINT}orphans/')
    assert orphans.status_code == status.HTTP_200_OK, show_status_and_response(orphans)
    orphan_ids = [o['id'] for o in orphans.json()]
    assert item_id in orphan_ids


def test_partial_update_item(boxitem_test_data):
    """Test partial update preserves other fields."""
    client = boxitem_test_data
    items = client.get(ENDPOINT).json()
    first_item = items[0]
    item_id = first_item['id']

    original = client.get(f'{ENDPOINT}{item_id}/').json()
    # BoxItemUpdate requires id in body
    response = client.patch(f'{ENDPOINT}{item_id}/', json={'id': item_id, 'name': 'Updated Item Name'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    updated = response.json()
    assert updated['name'] == 'Updated Item Name'
    assert updated['essential'] == original['essential']


class TestBoxItemsNotFound:
    """Test 404 responses for non-existent box items."""

    def test_read_one_not_found(self, boxitem_test_data):
        """GET /items/{id}/ returns 404 for non-existent item."""
        client = boxitem_test_data
        response = client.get(f'{ENDPOINT}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_delete_not_found(self, boxitem_test_data):
        """DELETE /items/{id}/ returns 404 for non-existent item."""
        client = boxitem_test_data
        response = client.delete(f'{ENDPOINT}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_update_not_found(self, boxitem_test_data):
        """PATCH /items/{id}/ returns 404 for non-existent item."""
        client = boxitem_test_data
        # BoxItemUpdate requires id in body
        response = client.patch(f'{ENDPOINT}99999/', json={'id': 99999, 'name': 'Does Not Exist'})
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)
