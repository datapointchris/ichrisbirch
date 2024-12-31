import pytest

import tests.util
from ichrisbirch import schemas

from .crud_test import ApiCrudTester


@pytest.fixture(autouse=True)
def insert_testing_data():
    tests.util.insert_test_data('boxes', 'boxitems')
    yield
    tests.util.delete_test_data('boxes', 'boxitems')


NEW_OBJ = schemas.BoxItemCreate(
    box_id=3,
    name='Pants',
    essential=True,
    warm=False,
    liquid=False,
)
ENDPOINT = '/box-packing/items/'
crud_tests = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ)


def test_read_one(test_api):
    crud_tests.test_read_one(test_api)


def test_read_many(test_api):
    crud_tests.test_read_many(test_api)


def test_create(test_api):
    """Box 3 is originally empty, all details set to false Adding an essential item should update the box essential
    detail to True.
    """
    box = schemas.Box(**test_api.get('/box-packing/boxes/3/').json())
    assert not box.essential
    crud_tests.test_create(test_api)
    box = schemas.Box(**test_api.get('/box-packing/boxes/3/').json())
    assert box.essential


def test_delete(test_api):
    """Box 1 liquid detail is True Deleting the liquid item should update the box liquid detail to False."""
    box = schemas.Box(**test_api.get('/box-packing/boxes/1/').json())
    assert box.liquid
    crud_tests.test_delete(test_api)
    box = schemas.Box(**test_api.get('/box-packing/boxes/1/').json())
    assert not box.liquid


def test_lifecycle(test_api):
    crud_tests.test_lifecycle(test_api)
