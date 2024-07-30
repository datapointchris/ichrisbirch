from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from fastapi import status

import tests.util
from ichrisbirch import schemas
from tests.util import show_status_and_response

from .crud_test import ApiCrudTester


@pytest.fixture(autouse=True)
def insert_testing_data():
    tests.util.insert_test_data('events')
    yield
    tests.util.delete_test_data('events')


NEW_OBJ = schemas.EventCreate(
    name='Event 4',
    date=datetime(2022, 10, 4, 20, 0),
    venue='Venue 4',
    url='https://example.com/event4',
    cost=40.0,
    attending=False,
    notes='Notes for Event 4',
)

ENDPOINT = '/events/'


crud_tests = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ)


def test_read_one(test_api):
    crud_tests.test_read_one(test_api)


def test_read_many(test_api):
    crud_tests.test_read_many(test_api)


def test_create(test_api):
    crud_tests.test_create(test_api)


def test_delete(test_api):
    crud_tests.test_delete(test_api)


def test_lifecycle(test_api):
    crud_tests.test_lifecycle(test_api)


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
    NEW_OBJ.date = event_date
    response = test_api.post(ENDPOINT, content=NEW_OBJ.model_dump_json())
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    event = test_api.get(f'{ENDPOINT}{response.json()["id"]}/')
    assert event.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert event.json()['date'] == output
