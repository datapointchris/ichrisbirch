import json

import pytest

from ichrisbirch import models
from ichrisbirch.api import endpoints


@pytest.fixture(scope='module')
def base_test_data():
    """Basic test data"""
    return [
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


test_data_for_create = [
    {
        'name': 'Task 4 Computer with notes priority 3',
        'notes': 'Notes task 4',
        'due_date': '2040-01-20',
    },
    {
        'name': 'Task 5 Chore without notes priority 20',
        'notes': None,
        'due_date': '2040-01-20',
    },
]


@pytest.fixture(scope='module')
def data_model():
    """Returns the SQLAlchemy model to use for the data"""
    return models.Countdown


@pytest.fixture(scope='module')
def router():
    """Returns the API router to use for this test module"""
    return endpoints.countdowns.router


@pytest.mark.parametrize('countdown_id', [1, 2, 3])
def test_read_one_countdown(postgres_testdb_in_docker, insert_test_data, test_api, countdown_id):
    """Test if able to read one countdown"""
    response = test_api.get(f'/countdowns/{countdown_id}/')
    assert response.status_code == 200


def test_read_many_countdowns(postgres_testdb_in_docker, insert_test_data, test_api):
    """Test if able to read many countdowns"""
    response = test_api.get('/countdowns/')
    assert response.status_code == 200
    assert len(response.json()) == 3


@pytest.mark.parametrize('test_countdown', test_data_for_create)
def test_create_countdown(postgres_testdb_in_docker, insert_test_data, test_api, test_countdown):
    """Test if able to create a countdown"""
    response = test_api.post('/countdowns/', data=json.dumps(test_countdown))
    assert response.status_code == 201
    assert dict(response.json())['name'] == test_countdown['name']

    # Test countdown was created
    response = test_api.get('/countdowns/')
    assert response.status_code == 200
    assert len(response.json()) == 4


@pytest.mark.parametrize('countdown_id', [1, 2, 3])
def test_delete_countdown(postgres_testdb_in_docker, insert_test_data, test_api, countdown_id):
    """Test if able to delete a countdown"""
    endpoint = f'/countdowns/{countdown_id}/'
    task = test_api.get(endpoint)
    response = test_api.delete(endpoint)
    deleted = test_api.get(endpoint)
    assert response.status_code == 200
    assert response.json() == task.json()
    assert deleted.status_code == 404


@pytest.mark.parametrize('test_countdown', test_data_for_create)
def test_countdown_lifecycle(postgres_testdb_in_docker, insert_test_data, test_api, test_countdown):
    """Integration test for CRUD lifecylce of a countdown"""

    # Read all countdowns
    all_countdowns = test_api.get('/countdowns/')
    assert all_countdowns.status_code == 200
    assert len(all_countdowns.json()) == 3

    # Create new countdown
    created_countdown = test_api.post('/countdowns/', data=json.dumps(test_countdown))
    assert created_countdown.status_code == 201
    assert created_countdown.json()['name'] == test_countdown['name']

    # Get created countdown
    countdown_id = created_countdown.json().get('id')
    endpoint = f'/countdowns/{countdown_id}/'
    response_countdown = test_api.get(endpoint)
    assert response_countdown.status_code == 200
    assert response_countdown.json()['name'] == test_countdown['name']

    # Read all countdowns with new countdown
    all_countdowns = test_api.get('/countdowns/')
    assert all_countdowns.status_code == 200
    assert len(all_countdowns.json()) == 4

    # Delete countdown
    deleted_countdown = test_api.delete(f'/countdowns/{countdown_id}/').json()
    assert deleted_countdown['name'] == test_countdown['name']

    # Make sure it's missing
    missing_countdown = test_api.get(f'/countdowns/{countdown_id}')
    assert missing_countdown.status_code == 404
