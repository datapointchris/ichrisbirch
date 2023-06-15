import pytest

from tests.helpers import show_status_and_response
from tests.testing_data.events import CREATE_DATA


@pytest.mark.parametrize('event_id', [1, 2, 3])
def test_read_one_event(test_api, event_id):
    response = test_api.get(f'/events/{event_id}/')
    assert response.status_code == 200, show_status_and_response(response)


def test_read_many_events(test_api):
    response = test_api.get('/events/')
    assert response.status_code == 200, show_status_and_response(response)
    assert len(response.json()) == 3


def test_create_event(test_api):
    response = test_api.post('/events/', json=CREATE_DATA)
    assert response.status_code == 201, show_status_and_response(response)
    assert dict(response.json())['name'] == CREATE_DATA['name']

    # Test event was created
    response = test_api.get('/events/')
    assert response.status_code == 200, show_status_and_response(response)
    assert len(response.json()) == 4


@pytest.mark.parametrize('event_id', [1, 2, 3])
def test_delete_event(test_api, event_id):
    endpoint = f'/events/{event_id}/'
    task = test_api.get(endpoint)
    assert task.status_code == 200, show_status_and_response(task)

    response = test_api.delete(endpoint)
    assert response.status_code == 204, show_status_and_response(response)

    deleted = test_api.get(endpoint)
    assert deleted.status_code == 404, show_status_and_response(deleted)


def test_event_lifecycle(test_api):
    """Integration test for CRUD lifecylce of a event"""

    # Read all events
    all_events = test_api.get('/events/')
    assert all_events.status_code == 200, show_status_and_response(all_events)
    assert len(all_events.json()) == 3

    # Create new event
    created_event = test_api.post('/events/', json=CREATE_DATA)
    assert created_event.status_code == 201, show_status_and_response(created_event)
    assert created_event.json()['name'] == CREATE_DATA['name']

    # Get created event
    event_id = created_event.json().get('id')
    endpoint = f'/events/{event_id}/'
    response_event = test_api.get(endpoint)
    assert response_event.status_code == 200, show_status_and_response(response_event)
    assert response_event.json()['name'] == CREATE_DATA['name']

    # Read all events with new event
    all_events = test_api.get('/events/')
    assert all_events.status_code == 200, show_status_and_response(all_events)
    assert len(all_events.json()) == 4

    # Delete event
    deleted_event = test_api.delete(f'/events/{event_id}/')
    assert deleted_event.status_code == 204, show_status_and_response(deleted_event)

    # Make sure it's missing
    missing_event = test_api.get(f'/events/{event_id}')
    assert missing_event.status_code == 404, show_status_and_response(missing_event)
