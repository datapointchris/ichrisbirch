from datetime import date

import pytest
from fastapi import status

import tests.util
from tests.util import show_status_and_response


@pytest.fixture(autouse=True)
def insert_testing_data():
    tests.util.insert_test_data('money_wasted')
    yield
    tests.util.delete_test_data('money_wasted')


NEW_OBJ = dict(
    item='Money Wasted on Junk Food',
    amount=12.34,
    date_wasted=date(2040, 1, 20),
)
ENDPOINT = '/money-wasted/'


def test_index(test_app_logged_in):
    response = test_app_logged_in.get(ENDPOINT)
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>Money Wasted</title>' in response.data


def test_add(test_app_logged_in):
    response = test_app_logged_in.post(ENDPOINT, data=NEW_OBJ | {'action': 'add'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>Money Wasted</title>' in response.data


def test_delete(test_app_logged_in):
    response = test_app_logged_in.post(ENDPOINT, data={'id': 1, 'action': 'delete'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>Money Wasted</title>' in response.data
