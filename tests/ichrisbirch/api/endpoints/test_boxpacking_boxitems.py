import pytest

from ichrisbirch import schemas
from tests.utils.database import delete_test_data
from tests.utils.database import insert_test_data

from .crud_test import ApiCrudTester


@pytest.fixture(autouse=True)
def insert_testing_data():
    insert_test_data('boxes')  # boxitems inserted via Box.items relationship
    yield
    delete_test_data('boxitems', 'boxes')  # Order matters: children first due to FK


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


def test_read_one(test_api_logged_in):
    # Use any box for basic CRUD tests
    boxes = test_api_logged_in.get('/box-packing/boxes/')
    first_box_id = boxes.json()[0]['id']
    crud_tester = create_crud_tester(first_box_id)
    crud_tester.test_read_one(test_api_logged_in)


def test_read_many(test_api_logged_in):
    boxes = test_api_logged_in.get('/box-packing/boxes/')
    first_box_id = boxes.json()[0]['id']
    crud_tester = create_crud_tester(first_box_id)
    crud_tester.test_read_many(test_api_logged_in)


def test_create(test_api_logged_in):
    """Adding an essential item to an empty box should update the box essential detail to True."""
    empty_box = get_empty_box(test_api_logged_in)
    box_id = empty_box['id']

    box = schemas.Box(**test_api_logged_in.get(f'/box-packing/boxes/{box_id}/').json())
    assert not box.essential

    crud_tester = create_crud_tester(box_id)
    crud_tester.test_create(test_api_logged_in)

    box = schemas.Box(**test_api_logged_in.get(f'/box-packing/boxes/{box_id}/').json())
    assert box.essential


def test_delete(test_api_logged_in):
    """Deleting the liquid item from a box should update the box liquid detail to False."""
    liquid_box = get_box_with_liquid_item(test_api_logged_in)
    box_id = liquid_box['id']

    box = schemas.Box(**test_api_logged_in.get(f'/box-packing/boxes/{box_id}/').json())
    assert box.liquid

    crud_tester = create_crud_tester(box_id)
    crud_tester.test_delete(test_api_logged_in)

    box = schemas.Box(**test_api_logged_in.get(f'/box-packing/boxes/{box_id}/').json())
    assert not box.liquid


def test_lifecycle(test_api_logged_in):
    boxes = test_api_logged_in.get('/box-packing/boxes/')
    first_box_id = boxes.json()[0]['id']
    crud_tester = create_crud_tester(first_box_id)
    crud_tester.test_lifecycle(test_api_logged_in)
