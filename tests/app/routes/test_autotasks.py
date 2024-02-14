from fastapi import status

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
    response = test_app.post('/autotasks/', data=data | {'method': 'add'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>AutoTasks</title>' in response.data

    # Expect that the autotask ran so it should have inserted the task into tasks table
    tasks_response = test_api.get('/tasks/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(tasks_response)
    assert len(tasks_response.json()) == 4


def test_delete_autotask(test_app):
    response = test_app.post('/autotasks/', data={'id': 1, 'method': 'delete'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>AutoTasks</title>' in response.data
