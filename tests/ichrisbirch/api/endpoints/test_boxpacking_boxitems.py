import pytest

from ichrisbirch import schemas
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
