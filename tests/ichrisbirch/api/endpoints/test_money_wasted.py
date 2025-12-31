from datetime import date

import pytest

from ichrisbirch import schemas
from tests.utils.database import insert_test_data_transactional

from .crud_test import ApiCrudTester

NEW_OBJ = schemas.MoneyWastedCreate(
    item='Money Wasted on Junk Food',
    amount=12.34,
    date_wasted=date(2040, 1, 20),
)

ENDPOINT = '/money-wasted/'


@pytest.fixture
def money_wasted_crud_tester(txn_api_logged_in):
    """Provide ApiCrudTester with transactional test data."""
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'money_wasted')
    crud_tester = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ, verify_attr='item')
    return client, crud_tester


def test_read_one(money_wasted_crud_tester):
    client, crud_tester = money_wasted_crud_tester
    crud_tester.test_read_one(client)


def test_read_many(money_wasted_crud_tester):
    client, crud_tester = money_wasted_crud_tester
    crud_tester.test_read_many(client)


def test_create(money_wasted_crud_tester):
    client, crud_tester = money_wasted_crud_tester
    crud_tester.test_create(client)


def test_delete(money_wasted_crud_tester):
    client, crud_tester = money_wasted_crud_tester
    crud_tester.test_delete(client)


def test_lifecycle(money_wasted_crud_tester):
    client, crud_tester = money_wasted_crud_tester
    crud_tester.test_lifecycle(client)
