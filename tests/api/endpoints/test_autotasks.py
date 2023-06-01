import json

import pytest

from ichrisbirch import models
from tests.helpers import show_status_and_response

BASE_DATA = [
    {
        'name': 'Task 1 Chore with notes priority 5 not completed',
        'notes': 'Notes for task 1',
        'category': 'Chore',
        'priority': 5,
        'frequency': 'Daily',
        'first_run_date': '2020-04-20 03:03:39.050648+00:00',
        'last_run_date': '2020-04-24 03:03:39.050648+00:00',
        'run_count': 5,
    },
    {
        'name': 'Task 2 Home without notes priority 10 not completed',
        'notes': None,
        'category': 'Home',
        'priority': 10,
        'frequency': 'Weekly',
        'first_run_date': '2020-03-20 03:03:39.050648+00:00',
        'last_run_date': '2020-03-24 03:03:39.050648+00:00',
        'run_count': 1,
    },
    {
        'name': 'Task 3 Home with notes priority 15 completed',
        'notes': 'Notes for task 3',
        'category': 'Home',
        'priority': 15,
        'frequency': 'Quarterly',
        'first_run_date': '2020-01-20 03:03:39.050648+00:00',
        'last_run_date': '2020-04-20 03:03:39.050648+00:00',
        'run_count': 2,
    },
]

CREATE_DATA = {
    'name': 'Task 4 Computer with notes priority 3',
    'notes': 'Notes task 4',
    'category': 'Computer',
    'priority': 3,
    'frequency': 'Biweekly',
}


@pytest.fixture(scope='function')
def test_data():
    """Basic test data"""
    return [models.AutoTask(**record) for record in BASE_DATA]


def test_read_one_autotask(insert_test_data, test_api):
    """Test if able to read one autotask"""
    response = test_api.get('/autotasks/1/')
    assert response.status_code == 200, show_status_and_response(response)
    response = test_api.get('/autotasks/2/')
    assert response.status_code == 200
    response = test_api.get('/autotasks/3/')
    assert response.status_code == 200


def test_read_many_autotasks(insert_test_data, test_api):
    """Test if able to read many autotasks"""
    response = test_api.get('/autotasks/')
    assert response.status_code == 200, show_status_and_response(response)
    assert len(response.json()) == 3


def test_create_autotask(insert_test_data, test_api):
    """Test if able to create a autotask"""
    response = test_api.post('/autotasks/', data=json.dumps(CREATE_DATA))
    assert response.status_code == 201, show_status_and_response(response)
    assert dict(response.json())['name'] == CREATE_DATA['name']

    # Test autotask was created
    response = test_api.get('/autotasks/')
    assert response.status_code == 200
    assert len(response.json()) == 4


def test_delete_autotask(insert_test_data, test_api):
    """Test if able to delete a autotask"""
    endpoint = '/autotasks/1/'
    task = test_api.get(endpoint)
    assert task.status_code == 200, show_status_and_response(task)

    response = test_api.delete(endpoint)
    assert response.status_code == 204, show_status_and_response(response)

    deleted = test_api.get(endpoint)
    assert deleted.status_code == 404, show_status_and_response(deleted)


def test_autotask_lifecycle(insert_test_data, test_api):
    """Integration test for CRUD lifecylce of a autotask"""

    # Read all autotasks
    all_autotasks = test_api.get('/autotasks/')
    assert all_autotasks.status_code == 200, show_status_and_response(all_autotasks)
    assert len(all_autotasks.json()) == 3

    # Create new task
    created_autotask = test_api.post('/autotasks/', data=json.dumps(CREATE_DATA))
    assert created_autotask.status_code == 201, show_status_and_response(created_autotask)
    assert created_autotask.json()['name'] == CREATE_DATA['name']

    # Get created task
    task_id = created_autotask.json().get('id')
    endpoint = f'/autotasks/{task_id}/'
    response_autotask = test_api.get(endpoint)
    assert response_autotask.status_code == 200, show_status_and_response(response_autotask)
    assert response_autotask.json()['name'] == CREATE_DATA['name']

    # Read all autotasks with new autotask
    all_autotasks = test_api.get('/autotasks/')
    assert all_autotasks.status_code == 200, show_status_and_response(all_autotasks)
    assert len(all_autotasks.json()) == 4

    # Delete Autotask
    deleted_autotask = test_api.delete(f'/autotasks/{task_id}/')
    assert deleted_autotask.status_code == 204, show_status_and_response(deleted_autotask)

    # Make sure it's missing
    missing_autotask = test_api.get(f'/autotasks/{task_id}')
    assert missing_autotask.status_code == 404, show_status_and_response(missing_autotask)
