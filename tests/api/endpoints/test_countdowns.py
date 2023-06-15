import pytest

from tests.helpers import show_status_and_response
from tests.testing_data.countdowns import CREATE_DATA


@pytest.mark.parametrize('countdown_id', [1, 2, 3])
def test_read_one_countdown(test_api, countdown_id):
    response = test_api.get(f'/countdowns/{countdown_id}/')
    assert response.status_code == 200, show_status_and_response(response)


def test_read_many_countdowns(test_api):
    response = test_api.get('/countdowns/')
    assert response.status_code == 200, show_status_and_response(response)
    assert len(response.json()) == 3


def test_create_countdown(test_api):
    response = test_api.post('/countdowns/', json=CREATE_DATA)
    assert response.status_code == 201, show_status_and_response(response)
    assert dict(response.json())['name'] == CREATE_DATA['name']

    # Test countdown was created
    response = test_api.get('/countdowns/')
    assert response.status_code == 200, show_status_and_response(response)
    assert len(response.json()) == 4


@pytest.mark.parametrize('countdown_id', [1, 2, 3])
def test_delete_countdown(test_api, countdown_id):
    endpoint = f'/countdowns/{countdown_id}/'
    task = test_api.get(endpoint)
    assert task.status_code == 200, show_status_and_response(task)

    response = test_api.delete(endpoint)
    assert response.status_code == 204, show_status_and_response(response)

    deleted = test_api.get(endpoint)
    assert deleted.status_code == 404, show_status_and_response(deleted)


def test_countdown_lifecycle(test_api):
    """Integration test for CRUD lifecylce of a countdown"""

    # Read all countdowns
    all_countdowns = test_api.get('/countdowns/')
    assert all_countdowns.status_code == 200, show_status_and_response(all_countdowns)
    assert len(all_countdowns.json()) == 3

    # Create new countdown
    created_countdown = test_api.post('/countdowns/', json=CREATE_DATA)
    assert created_countdown.status_code == 201, show_status_and_response(created_countdown)
    assert created_countdown.json()['name'] == CREATE_DATA['name']

    # Get created countdown
    countdown_id = created_countdown.json().get('id')
    endpoint = f'/countdowns/{countdown_id}/'
    response_countdown = test_api.get(endpoint)
    assert response_countdown.status_code == 200, show_status_and_response(response_countdown)
    assert response_countdown.json()['name'] == CREATE_DATA['name']

    # Read all countdowns with new countdown
    all_countdowns = test_api.get('/countdowns/')
    assert all_countdowns.status_code == 200, show_status_and_response(all_countdowns)
    assert len(all_countdowns.json()) == 4

    # Delete countdown
    deleted_countdown = test_api.delete(f'/countdowns/{countdown_id}/')
    assert deleted_countdown.status_code == 204, show_status_and_response(deleted_countdown)

    # Make sure it's missing
    missing_countdown = test_api.get(f'/countdowns/{countdown_id}')
    assert missing_countdown.status_code == 404, show_status_and_response(missing_countdown)
