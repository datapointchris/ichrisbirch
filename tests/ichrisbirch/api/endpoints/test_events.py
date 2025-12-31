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
