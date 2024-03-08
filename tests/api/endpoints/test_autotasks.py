import pytest
from fastapi import status

from ichrisbirch import schemas
from ichrisbirch.models.autotask import TaskFrequency
from ichrisbirch.models.task import TaskCategory
from tests.helpers import show_status_and_response

NEW_AUTOTASK = schemas.AutoTaskCreate(
    name='AutoTask 4 Computer with notes priority 3',
    notes='Notes task 4',
    category=TaskCategory.Computer,
    priority=3,
    frequency=TaskFrequency.Biweekly,
)


@pytest.mark.parametrize('autotask_id', [1, 2, 3])
def test_read_one_autotask(test_api, autotask_id):
    response = test_api.get(f'/autotasks/{autotask_id}/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


def test_read_many_autotasks(test_api):
    response = test_api.get('/autotasks/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 3


def test_create_autotask(test_api):
    response = test_api.post('/autotasks/', json=NEW_AUTOTASK.model_dump())
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    assert dict(response.json())['name'] == NEW_AUTOTASK.name

    # Test autotask was created
    response = test_api.get('/autotasks/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 4


@pytest.mark.parametrize('autotask_id', [1, 2, 3])
def test_delete_autotask(test_api, autotask_id):
    endpoint = f'/autotasks/{autotask_id}/'
    task = test_api.get(endpoint)
    assert task.status_code == status.HTTP_200_OK, show_status_and_response(task)

    response = test_api.delete(endpoint)
    assert response.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(response)

    deleted = test_api.get(endpoint)
    assert deleted.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(deleted)


def test_autotask_lifecycle(test_api):
    """Integration test for CRUD lifecylce of a autotask"""

    # Read all autotasks
    all_autotasks = test_api.get('/autotasks/')
    assert all_autotasks.status_code == status.HTTP_200_OK, show_status_and_response(all_autotasks)
    assert len(all_autotasks.json()) == 3

    # Create new autotask
    created_autotask = test_api.post('/autotasks/', json=NEW_AUTOTASK.model_dump())
    assert created_autotask.status_code == status.HTTP_201_CREATED, show_status_and_response(created_autotask)
    assert created_autotask.json()['name'] == NEW_AUTOTASK.name

    # Get created task
    task_id = created_autotask.json().get('id')
    endpoint = f'/autotasks/{task_id}/'
    response_autotask = test_api.get(endpoint)
    assert response_autotask.status_code == status.HTTP_200_OK, show_status_and_response(response_autotask)
    assert response_autotask.json()['name'] == NEW_AUTOTASK.name

    # Read all autotasks with new autotask
    all_autotasks = test_api.get('/autotasks/')
    assert all_autotasks.status_code == status.HTTP_200_OK, show_status_and_response(all_autotasks)
    assert len(all_autotasks.json()) == 4

    # Delete Autotask
    deleted_autotask = test_api.delete(f'/autotasks/{task_id}/')
    assert deleted_autotask.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(deleted_autotask)

    # Make sure it's missing
    missing_autotask = test_api.get(f'/autotasks/{task_id}')
    assert missing_autotask.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(missing_autotask)
