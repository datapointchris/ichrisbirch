import pytest
from fastapi import status

import tests.util
from ichrisbirch import schemas
from ichrisbirch.models.box import BoxSize
from tests.util import show_status_and_response

from .crud_test import ApiCrudTester


@pytest.fixture(autouse=True)
def insert_testing_data():
    tests.util.insert_test_data('boxes', 'boxitems')
    yield
    tests.util.delete_test_data('boxes', 'boxitems')


NEW_OBJ = schemas.BoxCreate(
    name='Box 4 - Bag of clothes',
    number=4,
    size=BoxSize.Bag,
    essential=True,
    warm=False,
    liquid=False,
)
ENDPOINT = '/box-packing/boxes/'
crud_tests = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ)


def test_read_one(test_api_logged_in):
    crud_tests.test_read_one(test_api_logged_in)


def test_read_many(test_api_logged_in):
    crud_tests.test_read_many(test_api_logged_in)


def test_create(test_api_logged_in):
    crud_tests.test_create(test_api_logged_in)


def test_delete(test_api_logged_in):
    crud_tests.test_delete(test_api_logged_in)


def test_lifecycle(test_api_logged_in):
    crud_tests.test_lifecycle(test_api_logged_in)


def test_search_box_items(test_api_logged_in):
    search_term = 'find'
    search_results = test_api_logged_in.get('/box-packing/search/', params={'q': search_term})
    assert search_results.status_code == status.HTTP_200_OK, show_status_and_response(search_results)
    assert len(search_results.json()) == 1

    search_term = 'home'
    search_results = test_api_logged_in.get('/box-packing/search/', params={'q': search_term})
    assert search_results.status_code == status.HTTP_200_OK, show_status_and_response(search_results)
    assert len(search_results.json()) == 0


# must explicitly use values because Sixteen = '16x16x16', where '16x16x16' is not valid Enum member name
@pytest.mark.parametrize('box_size', list(BoxSize))
def test_create_box_all_sizes(test_api_logged_in, box_size):
    test_box = schemas.BoxCreate(
        name='Box X',
        number=5,
        size=box_size,
        essential=True,
        warm=False,
        liquid=False,
    )
    response = test_api_logged_in.post(ENDPOINT, json=test_box.model_dump())
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    assert dict(response.json())['name'] == test_box.name


@pytest.mark.parametrize('essential', [True, False])
@pytest.mark.parametrize('warm', [True, False])
@pytest.mark.parametrize('liquid', [True, False])
def test_create_box_options_combinations(test_api_logged_in, essential, warm, liquid):
    test_box = schemas.BoxCreate(
        name='Box X',
        number=5,
        size=BoxSize.Large,
        essential=essential,
        warm=warm,
        liquid=liquid,
    )
    response = test_api_logged_in.post(ENDPOINT, json=test_box.model_dump())
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    assert dict(response.json())['name'] == test_box.name
