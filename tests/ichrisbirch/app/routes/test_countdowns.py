from datetime import date

import pytest
from fastapi import status

import tests.util
from tests.util import show_status_and_response


@pytest.fixture(autouse=True)
def insert_testing_data():
    tests.util.insert_test_data('countdowns')
    yield
    tests.util.delete_test_data('countdowns')


def test_index(test_app_logged_in):
    response = test_app_logged_in.get('/countdowns/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>Countdowns</title>' in response.data


def test_add_countdown(test_app_logged_in):
    data = dict(
        name='Countdown 4 Computer with notes priority 3',
        notes='Notes Countdown 4',
        due_date=date(2040, 1, 20).isoformat(),
    )
    response = test_app_logged_in.post('/countdowns/', data=data | {'action': 'add'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>Countdowns</title>' in response.data


def test_delete_countdown(test_app_logged_in):
    response = test_app_logged_in.post('/countdowns/', data={'id': 1, 'action': 'delete'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>Countdowns</title>' in response.data
