from datetime import date

import pytest

from ichrisbirch import schemas
from tests.utils.database import insert_test_data_transactional

from .crud_test import ApiCrudTester

ENDPOINT = '/countdowns/'
NEW_OBJ = schemas.CountdownCreate(
    name='Countdown 4 Computer with notes priority 3',
    notes='Notes Countdown 4',
    due_date=date(2040, 1, 20),
)


@pytest.fixture
def countdown_crud_tester(txn_api_logged_in):
    """Provide ApiCrudTester with transactional test data."""
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'countdowns')
    crud_tester = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ)
    return client, crud_tester


def test_read_one(countdown_crud_tester):
    client, crud_tester = countdown_crud_tester
    crud_tester.test_read_one(client)


def test_read_many(countdown_crud_tester):
    client, crud_tester = countdown_crud_tester
    crud_tester.test_read_many(client)


def test_create(countdown_crud_tester):
    client, crud_tester = countdown_crud_tester
    crud_tester.test_create(client)


def test_delete(countdown_crud_tester):
    client, crud_tester = countdown_crud_tester
    crud_tester.test_delete(client)


def test_lifecycle(countdown_crud_tester):
    client, crud_tester = countdown_crud_tester
    crud_tester.test_lifecycle(client)
