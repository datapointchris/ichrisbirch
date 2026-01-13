from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from fastapi import status

from ichrisbirch import schemas
from tests.util import show_status_and_response
from tests.utils.database import insert_test_data_transactional

from .crud_test import ApiCrudTester

NEW_OBJ = schemas.EventCreate(
    name='Event 4',
    date=datetime(2022, 10, 4, 20),
    venue='Venue 4',
    url='https://example.com/event4',
    cost=40.0,
    attending=False,
    notes='Notes for Event 4',
)

ENDPOINT = '/events/'


@pytest.fixture
def event_crud_tester(txn_api_logged_in):
    """Provide ApiCrudTester with transactional test data."""
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'events')
    crud_tester = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ)
    return client, crud_tester


def test_read_one(event_crud_tester):
    client, crud_tester = event_crud_tester
    crud_tester.test_read_one(client)


def test_read_many(event_crud_tester):
    client, crud_tester = event_crud_tester
    crud_tester.test_read_many(client)


def test_create(event_crud_tester):
    client, crud_tester = event_crud_tester
    crud_tester.test_create(client)


def test_delete(event_crud_tester):
    client, crud_tester = event_crud_tester
    crud_tester.test_delete(client)


def test_lifecycle(event_crud_tester):
    client, crud_tester = event_crud_tester
    crud_tester.test_lifecycle(client)


@pytest.mark.parametrize(
    ['event_date', 'output'],
    [
        (datetime(2022, 10, 4), '2022-10-04T00:00:00Z'),
        (datetime(2022, 10, 4, 12), '2022-10-04T12:00:00Z'),
        (datetime(2022, 10, 4, 12, tzinfo=ZoneInfo('America/Chicago')), '2022-10-04T17:00:00Z'),
        ('2022-10-04', '2022-10-04T00:00:00Z'),
        ('2022-10-04T12:00:00', '2022-10-04T12:00:00Z'),
        ('2022-10-04T12:00:00-05:00', '2022-10-04T17:00:00Z'),
    ],
)
def test_create_event_date_formats(txn_api_logged_in, event_date, output):
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'events')
    event_obj = schemas.EventCreate(
        name='Event Date Test',
        date=event_date,
        venue='Test Venue',
        url='https://example.com/test',
        cost=10.0,
        attending=False,
        notes='Date format test',
    )
    response = client.post(ENDPOINT, content=event_obj.model_dump_json())
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    event = client.get(f'{ENDPOINT}{response.json()["id"]}/')
    assert event.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert event.json()['date'] == output


def test_attend_event(event_crud_tester):
    """Test marking an event as attending."""
    client, crud_tester = event_crud_tester
    first_id = crud_tester.item_id_by_position(client, position=1)

    # Mark as attending
    response = client.patch(f'{ENDPOINT}{first_id}/attend/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert response.json()['attending'] is True

    # Verify persistence
    response = client.get(f'{ENDPOINT}{first_id}/')
    assert response.json()['attending'] is True


def test_partial_update(event_crud_tester):
    """Test partial update with only some fields."""
    client, crud_tester = event_crud_tester
    first_id = crud_tester.item_id_by_position(client, position=1)

    # Get original event
    original = client.get(f'{ENDPOINT}{first_id}/').json()

    # Update only venue
    response = client.patch(f'{ENDPOINT}{first_id}/', json={'venue': 'Updated Venue'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    updated = response.json()
    assert updated['venue'] == 'Updated Venue'
    assert updated['name'] == original['name']  # Other fields unchanged


class TestEventsNotFound:
    """Test 404 responses for non-existent events."""

    def test_read_one_not_found(self, event_crud_tester):
        """GET /{id}/ returns 404 for non-existent event."""
        client, _ = event_crud_tester
        response = client.get(f'{ENDPOINT}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_delete_not_found(self, event_crud_tester):
        """DELETE /{id}/ returns 404 for non-existent event."""
        client, _ = event_crud_tester
        response = client.delete(f'{ENDPOINT}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_update_not_found(self, event_crud_tester):
        """PATCH /{id}/ returns 404 for non-existent event."""
        client, _ = event_crud_tester
        response = client.patch(f'{ENDPOINT}99999/', json={'name': 'Does Not Exist'})
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_attend_not_found(self, event_crud_tester):
        """PATCH /{id}/attend/ returns 404 for non-existent event."""
        client, _ = event_crud_tester
        response = client.patch(f'{ENDPOINT}99999/attend/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)
