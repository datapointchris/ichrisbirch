from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from fastapi import status

import tests.util
from ichrisbirch import schemas
from tests.util import show_status_and_response


@pytest.fixture(autouse=True)
def insert_testing_data():
    tests.util.insert_test_data('events')


NEW_EVENT = schemas.EventCreate(
    name='Event 4',
    date=datetime(2022, 10, 4, 20, 0),
    venue='Venue 4',
    url='https://example.com/event4',
    cost=40.0,
    attending=False,
    notes='Notes for Event 4',
)


@pytest.mark.parametrize('event_id', [1, 2, 3])
def test_read_one_event(test_api, event_id):
    response = test_api.get(f'/events/{event_id}/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


def test_read_many_events(test_api):
    response = test_api.get('/events/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 3


def test_create_event(test_api):
    response = test_api.post('/events/', content=NEW_EVENT.model_dump_json())
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    assert dict(response.json())['name'] == NEW_EVENT.name

    # Test event was created
    response = test_api.get('/events/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 4


@pytest.mark.parametrize(
    ['event_date', 'output'],
    [
        (datetime(2022, 10, 4), '2022-10-04T00:00:00Z'),
        (datetime(2022, 10, 4, 12, 0, 0), '2022-10-04T12:00:00Z'),
        (datetime(2022, 10, 4, 12, 0, 0, tzinfo=ZoneInfo('America/Chicago')), '2022-10-04T17:00:00Z'),
        ('2022-10-04', '2022-10-04T00:00:00Z'),
        ('2022-10-04T12:00:00', '2022-10-04T12:00:00Z'),
        ('2022-10-04T12:00:00-05:00', '2022-10-04T17:00:00Z'),
    ],
)
def test_create_event_date_formats(test_api, event_date, output):
    NEW_EVENT.date = event_date
    response = test_api.post('/events/', content=NEW_EVENT.model_dump_json())
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    event = test_api.get(f'/events/{response.json()["id"]}/')
    assert event.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert event.json()['date'] == output


@pytest.mark.parametrize('event_id', [1, 2, 3])
def test_delete_event(test_api, event_id):
    endpoint = f'/events/{event_id}/'
    task = test_api.get(endpoint)
    assert task.status_code == status.HTTP_200_OK, show_status_and_response(task)

    response = test_api.delete(endpoint)
    assert response.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(response)

    deleted = test_api.get(endpoint)
    assert deleted.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(deleted)


def test_event_lifecycle(test_api):
    """Integration test for CRUD lifecylce of a event."""

    # Read all events
    all_events = test_api.get('/events/')
    assert all_events.status_code == status.HTTP_200_OK, show_status_and_response(all_events)
    assert len(all_events.json()) == 3

    # Create new event
    created_event = test_api.post('/events/', content=NEW_EVENT.model_dump_json())
    assert created_event.status_code == status.HTTP_201_CREATED, show_status_and_response(created_event)
    assert created_event.json()['name'] == NEW_EVENT.name

    # Get created event
    event_id = created_event.json().get('id')
    endpoint = f'/events/{event_id}/'
    response_event = test_api.get(endpoint)
    assert response_event.status_code == status.HTTP_200_OK, show_status_and_response(response_event)
    assert response_event.json()['name'] == NEW_EVENT.name

    # Read all events with new event
    all_events = test_api.get('/events/')
    assert all_events.status_code == status.HTTP_200_OK, show_status_and_response(all_events)
    assert len(all_events.json()) == 4

    # Delete event
    deleted_event = test_api.delete(f'/events/{event_id}/')
    assert deleted_event.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(deleted_event)

    # Make sure it's missing
    missing_event = test_api.get(f'/events/{event_id}')
    assert missing_event.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(missing_event)
