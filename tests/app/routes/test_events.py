from datetime import datetime

import pytest
import requests
from fastapi import status

from tests.helpers import show_status_and_response


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
            method='add',
        ),
    )
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>Events</title>' in response.data


def test_add_event_missing_attending_field(test_app):
    with pytest.raises(requests.exceptions.HTTPError):
        test_app.post(
            '/events/',
            data=dict(
                name='Error for missing attending field',
                date=datetime(2022, 10, 4, 20, 0).isoformat(),
                venue='Venue 4',
                url='https://example.com/event4',
                cost=40.0,
                notes='Notes for Error for missing attending field',
                method='add',
            ),
        )


def test_delete_event(test_app):
    response = test_app.post('/events/', data={'id': 1, 'method': 'delete'})
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
            method='bad',
        ),
    )
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
