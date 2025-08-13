from datetime import datetime

import httpx
import pytest
from fastapi import status

from tests.util import show_status_and_response
from tests.utils.database import delete_test_data
from tests.utils.database import insert_test_data


@pytest.fixture(autouse=True)
def insert_testing_data():
    insert_test_data('events')
    yield
    delete_test_data('events')


def test_index(test_app_logged_in):
    response = test_app_logged_in.get('/events/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>Events</title>' in response.data


def test_add_event(test_app_logged_in):
    response = test_app_logged_in.post(
        '/events/',
        data=dict(
            name='Event 4',
            date=datetime(2022, 10, 4, 20, 0).isoformat(),
            venue='Venue 4',
            url='https://example.com/event4',
            cost=40.0,
            attending=False,
            notes='Notes for Event 4',
            action='add',
        ),
    )
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>Events</title>' in response.data


# TODO: Grab some logs or something instead of testing for the exception, maybe test in the api
@pytest.mark.skip(reason='Flask app swallows the error and logs it but does not raise an exception')
def test_add_event_missing_attending_field(test_app_logged_in):
    with pytest.raises(httpx.HTTPError):
        test_app_logged_in.post(
            '/events/',
            data=dict(
                name='Should give validation error',
                date=datetime(2022, 10, 4, 20, 0).isoformat(),
                venue='Venue 4',
                url='https://example.com/event4',
                cost=40.0,
                notes='Should raise 422 Unprocessable Entity error because of missing attending field',
                action='add',
            ),
        )


def test_delete_event(test_app_logged_in):
    response = test_app_logged_in.post('/events/', data={'id': 1, 'action': 'delete'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>Events</title>' in response.data


def test_send_bad_method(test_app_logged_in):
    response = test_app_logged_in.post(
        '/events/',
        data=dict(
            name='Event 4',
            date=datetime(2022, 10, 4, 20, 0).isoformat(),
            venue='Venue 4',
            url='https://example.com/event4',
            cost=40.0,
            attending=False,
            notes='Notes for Event 4',
            action='bad_method_type',
        ),
    )
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
