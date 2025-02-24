from datetime import date

import pytest

import tests.util
from ichrisbirch import schemas

from .crud_test import ApiCrudTester


@pytest.fixture(autouse=True)
def insert_testing_data():
    tests.util.insert_test_data('money_wasted')
    yield
    tests.util.delete_test_data('money_wasted')


NEW_OBJ = schemas.MoneyWastedCreate(
    item='Money Wasted on Junk Food',
    amount=12.34,
    date_wasted=date(2040, 1, 20),
)

ENDPOINT = '/money-wasted/'


crud_tests = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ)


def test_read_one(test_api_logged_in):
    crud_tests.test_read_one(test_api_logged_in)


def test_read_many(test_api_logged_in):
    crud_tests.test_read_many(test_api_logged_in)


def test_create(test_api_logged_in):
    crud_tests.test_create(test_api_logged_in, verify_attr='item')


def test_delete(test_api_logged_in):
    crud_tests.test_delete(test_api_logged_in)


def test_lifecycle(test_api_logged_in):
    crud_tests.test_lifecycle(test_api_logged_in, verify_attr='item')
