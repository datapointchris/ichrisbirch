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
            'category': 'Chore',
            'priority': 5,
            'frequency': 'Daily',
            'first_run_date': '2020-04-20 03:03:39.050648+00:00',
            'last_run_date': '2020-04-24 03:03:39.050648+00:00',
            'run_count': '5',
        },
        {
            'name': 'Task 2 Home without notes priority 10 not completed',
            'notes': None,
            'category': 'Home',
            'priority': 10,
            'frequency': 'Weekly',
            'first_run_date': '2020-03-20 03:03:39.050648+00:00',
            'last_run_date': '2020-03-24 03:03:39.050648+00:00',
            'run_count': '1',
        },
        {
            'name': 'Task 3 Home with notes priority 15 completed',
            'notes': 'Notes for task 3',
            'category': 'Home',
            'priority': 15,
            'frequency': 'Quarterly',
            'first_run_date': '2020-01-20 03:03:39.050648+00:00',
            'last_run_date': '2020-04-20 03:03:39.050648+00:00',
            'run_count': '2',
        },
    ]


test_data_for_create = [
    {
        'name': 'Task 4 Computer with notes priority 3',
        'notes': 'Notes task 4',
        'category': 'Computer',
        'priority': 3,
        'frequency': 'Biweekly',
    },
    {
        'name': 'Task 5 Chore without notes priority 20',
        'notes': None,
        'category': 'Chore',
        'priority': 20,
        'frequency': 'Semiannual',
    },
]


@pytest.fixture(scope='module')
def data_model():
    """Returns the SQLAlchemy model to use for the data"""
    return models.AutoTask


@pytest.fixture(scope='module')
def router():
    """Returns the API router to use for this test module"""
    return endpoints.autotasks.router


@pytest.mark.parametrize('task_id', [1, 2, 3])
def test_read_one_autotask(postgres_testdb_in_docker, insert_test_data, test_api, task_id):
    """Test if able to read one autotask"""
    response = test_api.get(f'/autotasks/{task_id}/')
    assert response.status_code == 200


def test_read_many_autotasks(postgres_testdb_in_docker, insert_test_data, test_api):
    """Test if able to read many autotasks"""
    response = test_api.get('/autotasks/')
    assert response.status_code == 200
    assert len(response.json()) == 3


@pytest.mark.parametrize('test_autotask', test_data_for_create)
def test_create_autotask(postgres_testdb_in_docker, insert_test_data, test_api, test_autotask):
    """Test if able to create a autotask"""
    response = test_api.post('/autotasks/', data=json.dumps(test_autotask))
    assert response.status_code == 201
    assert dict(response.json())['name'] == test_autotask['name']

    # Test autotask was created
    response = test_api.get('/autotasks/')
    assert response.status_code == 200
    assert len(response.json()) == 4


@pytest.mark.parametrize('task_id', [1, 2, 3])
def test_delete_autotask(postgres_testdb_in_docker, insert_test_data, test_api, task_id):
    """Test if able to delete a autotask"""
    endpoint = f'/autotasks/{task_id}/'
    task = test_api.get(endpoint)
    response = test_api.delete(endpoint)
    deleted = test_api.get(endpoint)
    assert response.status_code == 200
    assert response.json() == task.json()
    assert deleted.status_code == 404


@pytest.mark.parametrize('test_autotask', test_data_for_create)
def test_autotask_lifecycle(postgres_testdb_in_docker, insert_test_data, test_api, test_autotask):
    """Integration test for CRUD lifecylce of a autotask"""

    # Read all autotasks
    all_autotasks = test_api.get('/autotasks/')
    assert all_autotasks.status_code == 200
    assert len(all_autotasks.json()) == 3

    # Create new task
    created_autotask = test_api.post('/autotasks/', data=json.dumps(test_autotask))
    assert created_autotask.status_code == 201
    assert created_autotask.json()['name'] == test_autotask['name']

    # Get created task
    task_id = created_autotask.json().get('id')
    endpoint = f'/autotasks/{task_id}/'
    response_autotask = test_api.get(endpoint)
    assert response_autotask.status_code == 200
    assert response_autotask.json()['name'] == test_autotask['name']

    # Read all autotasks with new autotask
    all_autotasks = test_api.get('/autotasks/')
    assert all_autotasks.status_code == 200
    assert len(all_autotasks.json()) == 4

    # Delete Autotask
    deleted_autotask = test_api.delete(f'/autotasks/{task_id}/').json()
    assert deleted_autotask['name'] == test_autotask['name']

    # Make sure it's missing
    missing_autotask = test_api.get(f'/autotasks/{task_id}')
    assert missing_autotask.status_code == 404
