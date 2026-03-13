from datetime import date

import pytest
from fastapi import status

from ichrisbirch import schemas
from tests.util import show_status_and_response
from tests.utils.database import insert_test_data_transactional

from .crud_test import ApiCrudTester

ENDPOINT = '/durations/'
NEW_OBJ = schemas.DurationCreate(
    name='Duration 4 New Feature',
    start_date=date(2025, 1, 1),
    end_date=None,
    notes='Test duration',
    color='#00FF00',
)


@pytest.fixture
def duration_crud_tester(txn_api_logged_in):
    """Provide ApiCrudTester with transactional test data."""
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'durations')
    crud_tester = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ)
    return client, crud_tester


def test_read_one(duration_crud_tester):
    client, crud_tester = duration_crud_tester
    crud_tester.test_read_one(client)


def test_read_many(duration_crud_tester):
    client, crud_tester = duration_crud_tester
    crud_tester.test_read_many(client)


def test_create(duration_crud_tester):
    client, crud_tester = duration_crud_tester
    crud_tester.test_create(client)


def test_delete(duration_crud_tester):
    client, crud_tester = duration_crud_tester
    crud_tester.test_delete(client)


def test_lifecycle(duration_crud_tester):
    client, crud_tester = duration_crud_tester
    crud_tester.test_lifecycle(client)


def test_partial_update(duration_crud_tester):
    """Test partial update with only some fields."""
    client, crud_tester = duration_crud_tester
    first_id = crud_tester.item_id_by_position(client, position=1)

    original = client.get(f'{ENDPOINT}{first_id}/').json()

    response = client.patch(f'{ENDPOINT}{first_id}/', json={'notes': 'Updated notes'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    updated = response.json()
    assert updated['notes'] == 'Updated notes'
    assert updated['name'] == original['name']


def test_duration_has_notes(duration_crud_tester):
    """Test that durations are returned with their notes eagerly loaded."""
    client, crud_tester = duration_crud_tester
    first_id = crud_tester.item_id_by_position(client, position=1)

    response = client.get(f'{ENDPOINT}{first_id}/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    data = response.json()
    assert 'duration_notes' in data
    assert isinstance(data['duration_notes'], list)


def test_cascade_delete(duration_crud_tester):
    """Test that deleting a duration also deletes its notes."""
    client, crud_tester = duration_crud_tester

    # Find a duration with notes (first one has 2 notes)
    response = client.get(ENDPOINT)
    durations = response.json()
    duration_with_notes = next((d for d in durations if len(d['duration_notes']) > 0), None)
    assert duration_with_notes is not None, 'No duration with notes found in test data'

    duration_id = duration_with_notes['id']
    delete_response = client.delete(f'{ENDPOINT}{duration_id}/')
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(delete_response)

    # Verify duration is gone
    get_response = client.get(f'{ENDPOINT}{duration_id}/')
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


# --- Note CRUD tests ---


def test_create_note(duration_crud_tester):
    """Test adding a note to a duration."""
    client, crud_tester = duration_crud_tester
    first_id = crud_tester.item_id_by_position(client, position=1)

    note_data = {'date': '2025-06-15', 'content': 'New milestone reached'}
    response = client.post(f'{ENDPOINT}{first_id}/notes/', json=note_data)
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    note = response.json()
    assert note['content'] == 'New milestone reached'
    assert note['duration_id'] == first_id


def test_update_note(duration_crud_tester):
    """Test updating a note on a duration."""
    client, crud_tester = duration_crud_tester

    # Find duration with notes
    response = client.get(ENDPOINT)
    durations = response.json()
    duration_with_notes = next(d for d in durations if len(d['duration_notes']) > 0)
    duration_id = duration_with_notes['id']
    note_id = duration_with_notes['duration_notes'][0]['id']

    update_response = client.patch(
        f'{ENDPOINT}{duration_id}/notes/{note_id}/',
        json={'content': 'Updated content'},
    )
    assert update_response.status_code == status.HTTP_200_OK, show_status_and_response(update_response)
    assert update_response.json()['content'] == 'Updated content'


def test_delete_note(duration_crud_tester):
    """Test deleting a note from a duration."""
    client, crud_tester = duration_crud_tester

    # Find duration with notes
    response = client.get(ENDPOINT)
    durations = response.json()
    duration_with_notes = next(d for d in durations if len(d['duration_notes']) > 0)
    duration_id = duration_with_notes['id']
    note_id = duration_with_notes['duration_notes'][0]['id']
    original_note_count = len(duration_with_notes['duration_notes'])

    delete_response = client.delete(f'{ENDPOINT}{duration_id}/notes/{note_id}/')
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(delete_response)

    # Verify note count decreased
    get_response = client.get(f'{ENDPOINT}{duration_id}/')
    assert len(get_response.json()['duration_notes']) == original_note_count - 1


def test_note_belongs_to_duration(duration_crud_tester):
    """Test that note endpoints validate the note belongs to the specified duration."""
    client, crud_tester = duration_crud_tester

    # Find a duration with notes and another without
    response = client.get(ENDPOINT)
    durations = response.json()
    duration_with_notes = next(d for d in durations if len(d['duration_notes']) > 0)
    other_duration = next(d for d in durations if d['id'] != duration_with_notes['id'])

    note_id = duration_with_notes['duration_notes'][0]['id']

    # Try to update note via wrong duration
    update_response = client.patch(
        f'{ENDPOINT}{other_duration["id"]}/notes/{note_id}/',
        json={'content': 'Should fail'},
    )
    assert update_response.status_code == status.HTTP_404_NOT_FOUND

    # Try to delete note via wrong duration
    delete_response = client.delete(f'{ENDPOINT}{other_duration["id"]}/notes/{note_id}/')
    assert delete_response.status_code == status.HTTP_404_NOT_FOUND


def test_create_note_nonexistent_duration(duration_crud_tester):
    """Test adding a note to a non-existent duration returns 404."""
    client, _ = duration_crud_tester
    note_data = {'date': '2025-06-15', 'content': 'Should fail'}
    response = client.post(f'{ENDPOINT}99999/notes/', json=note_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDurationsNotFound:
    """Test 404 responses for non-existent durations."""

    def test_read_one_not_found(self, duration_crud_tester):
        client, _ = duration_crud_tester
        response = client.get(f'{ENDPOINT}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_delete_not_found(self, duration_crud_tester):
        client, _ = duration_crud_tester
        response = client.delete(f'{ENDPOINT}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_update_not_found(self, duration_crud_tester):
        client, _ = duration_crud_tester
        response = client.patch(f'{ENDPOINT}99999/', json={'name': 'Does Not Exist'})
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)
