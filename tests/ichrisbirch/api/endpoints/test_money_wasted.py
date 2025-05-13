from datetime import date

import pytest

from ichrisbirch import schemas
from tests.utils.database import delete_test_data
from tests.utils.database import insert_test_data

from .crud_test import ApiCrudTester


@pytest.fixture(autouse=True)
def insert_testing_data():
    insert_test_data('money_wasted')
    yield
    delete_test_data('money_wasted')


NEW_OBJ = schemas.MoneyWastedCreate(
    item='Money Wasted on Junk Food',
    amount=12.34,
    date_wasted=date(2040, 1, 20),
)

ENDPOINT = '/money-wasted/'


crud_tests = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ, verify_attr='item')


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
