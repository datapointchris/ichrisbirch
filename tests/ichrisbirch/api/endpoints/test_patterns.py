import pytest
from fastapi import status

from ichrisbirch import schemas
from tests.util import show_status_and_response
from tests.utils.database import insert_test_data_transactional

from .crud_test import ApiCrudTester

ENDPOINT = '/patterns/'
NEW_OBJ = schemas.PatternCreate(message='Pattern 4, skipped breakfast and was snappy by 11am')


@pytest.fixture
def pattern_crud_tester(txn_api_logged_in):
    """Provide ApiCrudTester with transactional test data."""
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'patterns')
    crud_tester = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ, verify_attr='message')
    return client, crud_tester


def test_read_one(pattern_crud_tester):
    client, crud_tester = pattern_crud_tester
    crud_tester.test_read_one(client)


def test_read_many(pattern_crud_tester):
    client, crud_tester = pattern_crud_tester
    crud_tester.test_read_many(client)


def test_create(pattern_crud_tester):
    client, crud_tester = pattern_crud_tester
    crud_tester.test_create(client)


def test_delete(pattern_crud_tester):
    client, crud_tester = pattern_crud_tester
    crud_tester.test_delete(client)


def test_lifecycle(pattern_crud_tester):
    client, crud_tester = pattern_crud_tester
    crud_tester.test_lifecycle(client)


def test_create_without_recorded_at_stamps_now(pattern_crud_tester):
    """Capturing is one argument — the server supplies the timestamp."""
    client, _ = pattern_crud_tester
    response = client.post(ENDPOINT, json={'message': 'no timestamp supplied'})
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    assert response.json()['recorded_at'] is not None


def test_create_honours_a_supplied_recorded_at(pattern_crud_tester):
    """The dotfiles JSONL import needs entries filed at the time they were written."""
    client, _ = pattern_crud_tester
    response = client.post(ENDPOINT, json={'message': 'imported entry', 'recorded_at': '2025-12-11T22:34:40+00:00'})
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    assert response.json()['recorded_at'].startswith('2025-12-11T22:34:40')


def test_read_many_is_newest_first(pattern_crud_tester):
    client, _ = pattern_crud_tester
    response = client.get(ENDPOINT)
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    recorded = [entry['recorded_at'] for entry in response.json()]
    assert recorded == sorted(recorded, reverse=True)


def test_search_filters_by_message(pattern_crud_tester):
    client, _ = pattern_crud_tester
    response = client.get(ENDPOINT, params={'search': 'heartburn'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    results = response.json()
    assert len(results) == 1
    assert 'heartburn' in results[0]['message']


def test_search_is_case_insensitive(pattern_crud_tester):
    client, _ = pattern_crud_tester
    response = client.get(ENDPOINT, params={'search': 'HEARTBURN'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 1


def test_limit_caps_the_result_set(pattern_crud_tester):
    client, _ = pattern_crud_tester
    response = client.get(ENDPOINT, params={'limit': 2})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 2
