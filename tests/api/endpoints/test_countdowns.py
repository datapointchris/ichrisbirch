import json

import pytest

from ichrisbirch import models
from tests.helpers import show_status_and_response

BASE_DATA = [
    {
        'name': 'Task 1 Chore with notes priority 5 not completed',
        'notes': 'Notes for task 1',
        'due_date': '2020-04-24',
    },
    {
        'name': 'Task 2 Home without notes priority 10 not completed',
        'notes': None,
        'due_date': '2050-03-20',
    },
    {
        'name': 'Task 3 Home with notes priority 15 completed',
        'notes': 'Notes for task 3',
        'due_date': '2050-01-20',
    },
]

CREATE_DATA = {
    'name': 'Task 4 Computer with notes priority 3',
    'notes': 'Notes task 4',
    'due_date': '2040-01-20',
}


@pytest.fixture(scope='function')
def test_data():
    """Basic test data"""
    return [models.Countdown(**record) for record in BASE_DATA]


def test_read_one_countdown(insert_test_data, test_api):
    """Test if able to read one countdown"""
    response = test_api.get('/countdowns/1/')
    assert response.status_code == 200, show_status_and_response(response)


def test_read_many_countdowns(insert_test_data, test_api):
    """Test if able to read many countdowns"""
    response = test_api.get('/countdowns/')
    assert response.status_code == 200, show_status_and_response(response)
    assert len(response.json()) == 3


def test_create_countdown(insert_test_data, test_api):
    """Test if able to create a countdown"""
    response = test_api.post('/countdowns/', data=json.dumps(CREATE_DATA))
    assert response.status_code == 201, show_status_and_response(response)
    assert dict(response.json())['name'] == CREATE_DATA['name']

    # Test countdown was created
    response = test_api.get('/countdowns/')
    assert response.status_code == 200, show_status_and_response(response)
    assert len(response.json()) == 4


@pytest.mark.parametrize('countdown_id', [1, 2, 3])
def test_delete_countdown(insert_test_data, test_api, countdown_id):
    """Test if able to delete a countdown"""
    endpoint = f'/countdowns/{countdown_id}/'
    task = test_api.get(endpoint)
    assert task.status_code == 200, show_status_and_response(task)

    response = test_api.delete(endpoint)
    assert response.status_code == 204, show_status_and_response(response)

    deleted = test_api.get(endpoint)
    assert deleted.status_code == 404, show_status_and_response(deleted)


def test_countdown_lifecycle(insert_test_data, test_api):
    """Integration test for CRUD lifecylce of a countdown"""

    # Read all countdowns
    all_countdowns = test_api.get('/countdowns/')
    assert all_countdowns.status_code == 200, show_status_and_response(all_countdowns)
    assert len(all_countdowns.json()) == 3

    # Create new countdown
    created_countdown = test_api.post('/countdowns/', data=json.dumps(CREATE_DATA))
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
