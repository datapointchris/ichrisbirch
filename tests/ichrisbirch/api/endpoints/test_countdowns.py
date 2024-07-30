from datetime import date

import pytest

import tests.util
from ichrisbirch import schemas

from .crud_test import ApiCrudTester


@pytest.fixture(autouse=True)
def insert_testing_data():
    tests.util.insert_test_data('countdowns')
    yield
    tests.util.delete_test_data('countdowns')


NEW_OBJ = schemas.CountdownCreate(
    name='Countdown 4 Computer with notes priority 3',
    notes='Notes Countdown 4',
    due_date=date(2040, 1, 20),
)

ENDPOINT = '/countdowns/'


crud_tests = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ)


def test_read_one(test_api):
    crud_tests.test_read_one(test_api)


def test_read_many(test_api):
    crud_tests.test_read_many(test_api)


def test_create(test_api):
    crud_tests.test_create(test_api)


def test_delete(test_api):
    crud_tests.test_delete(test_api)


def test_lifecycle(test_api):
    crud_tests.test_lifecycle(test_api)
