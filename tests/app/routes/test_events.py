from datetime import datetime

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
            action='add',
        ),
    )
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>Events</title>' in response.data


def test_add_event_missing_attending_field(test_app):
    response = test_app.post(
        '/events/',
        data=dict(
            name='Should redirect from validation error',
            date=datetime(2022, 10, 4, 20, 0).isoformat(),
            venue='Venue 4',
            url='https://example.com/event4',
            cost=40.0,
            notes='400 status code is caught and flashed and logged, request is redirected',
            action='add',
        ),
    )
    assert response.status_code == status.HTTP_302_FOUND, show_status_and_response(response)


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
