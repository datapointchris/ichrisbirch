import pytest
from fastapi import status

from ichrisbirch import schemas
from ichrisbirch.models.autotask import TaskFrequency
from ichrisbirch.models.task import TaskCategory
from tests.helpers import show_status_and_response


def test_index(test_app):
    response = test_app.get('/autotasks/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>AutoTasks</title>' in response.data


def test_add_autotask(test_app, test_api):
    """Test add a new autotask

    Expected: Both create an autotask AND run it, which will create a new task
    """
    data = dict(
        name='AutoTask 4 Computer with notes priority 3',
        notes='Notes task 4',
        category=TaskCategory.Computer.value,
        priority=3,
        frequency=TaskFrequency.Biweekly.value,
    )
    response = test_app.post('/autotasks/', data=data | {'action': 'add'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>AutoTasks</title>' in response.data

    # Expect that the autotask ran so it should have inserted the task into tasks table
    tasks_response = test_api.get('/tasks/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(tasks_response)
    assert len(tasks_response.json()) == 4


def test_delete_autotask(test_app):
    response = test_app.post('/autotasks/', data={'id': 1, 'action': 'delete'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>AutoTasks</title>' in response.data


@pytest.mark.parametrize('category', list(TaskCategory))
def test_task_categories(test_api, category):
    test_autotask = schemas.AutoTaskCreate(
        name='AutoTask 4 Computer with notes priority 3',
        notes='Notes task 4',
        category=category,
        priority=3,
        frequency=TaskFrequency.Biweekly,
    )
    created_autotask = test_api.post('/autotasks/', json=test_autotask.model_dump())
    assert created_autotask.status_code == status.HTTP_201_CREATED, show_status_and_response(created_autotask)
    assert created_autotask.json()['name'] == test_autotask.name


@pytest.mark.parametrize('frequency', list(TaskFrequency))
def test_autotask_frequency(test_api, frequency):
    test_autotask = schemas.AutoTaskCreate(
        name='AutoTask 4 Computer with notes priority 3',
        notes='Notes task 4',
        category=TaskCategory.Personal,
        priority=3,
        frequency=frequency,
    )
    created_autotask = test_api.post('/autotasks/', json=test_autotask.model_dump())
    assert created_autotask.status_code == status.HTTP_201_CREATED, show_status_and_response(created_autotask)
    assert created_autotask.json()['name'] == test_autotask.name
