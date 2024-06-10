from datetime import datetime

import httpx
import pytest
from fastapi import status

import tests.util
from tests.util import show_status_and_response


@pytest.fixture(autouse=True)
def insert_testing_data():
    tests.util.insert_test_data('events')


def test_index(test_app):
    response = test_app.get('/events/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>Events</title>' in response.data


def test_add_event(test_app):
    response = test_app.post(
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


def test_add_event_missing_attending_field(test_app):
    with pytest.raises(httpx.HTTPError):
        test_app.post(
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


def test_delete_event(test_app):
    response = test_app.post('/events/', data={'id': 1, 'action': 'delete'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>Events</title>' in response.data


def test_send_bad_method(test_app):
    response = test_app.post(
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
