import pytest

from ichrisbirch import models
from tests.helpers import show_status_and_response
from tests.testing_data.autotasks import AUTOTASK_TEST_CREATE_DATA, AUTOTASK_TEST_DATA


@pytest.fixture(scope='function')
def test_data():
    """Basic test data"""
    return [models.AutoTask(**record) for record in AUTOTASK_TEST_DATA]


@pytest.mark.parametrize('autotask_id', [1, 2, 3])
def test_read_one_autotask(insert_test_data, test_api, autotask_id):
    """Test if able to read one autotask"""
    response = test_api.get(f'/autotasks/{autotask_id}/')
    assert response.status_code == 200, show_status_and_response(response)


def test_read_many_autotasks(insert_test_data, test_api):
    """Test if able to read many autotasks"""
    response = test_api.get('/autotasks/')
    assert response.status_code == 200, show_status_and_response(response)
    assert len(response.json()) == 3


def test_create_autotask(insert_test_data, test_api):
    """Test if able to create a autotask"""
    response = test_api.post('/autotasks/', json=AUTOTASK_TEST_CREATE_DATA)
    assert response.status_code == 201, show_status_and_response(response)
    assert dict(response.json())['name'] == AUTOTASK_TEST_CREATE_DATA['name']

    # Test autotask was created
    response = test_api.get('/autotasks/')
    assert response.status_code == 200, show_status_and_response(response)
    assert len(response.json()) == 4


@pytest.mark.parametrize('autotask_id', [1, 2, 3])
def test_delete_autotask(insert_test_data, test_api, autotask_id):
    """Test if able to delete a autotask"""
    endpoint = f'/autotasks/{autotask_id}/'
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
    created_autotask = test_api.post('/autotasks/', json=AUTOTASK_TEST_CREATE_DATA)
    assert created_autotask.status_code == 201, show_status_and_response(created_autotask)
    assert created_autotask.json()['name'] == AUTOTASK_TEST_CREATE_DATA['name']

    # Get created task
    task_id = created_autotask.json().get('id')
    endpoint = f'/autotasks/{task_id}/'
    response_autotask = test_api.get(endpoint)
    assert response_autotask.status_code == 200, show_status_and_response(response_autotask)
    assert response_autotask.json()['name'] == AUTOTASK_TEST_CREATE_DATA['name']

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
