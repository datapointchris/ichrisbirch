from ichrisbirch.models.autotask import TaskFrequency
from ichrisbirch.models.task import TaskCategory
from tests.helpers import show_status_and_response


def test_index(test_app):
    """Test the index page"""
    response = test_app.get('/autotasks/')
    assert response.status_code == 200
    assert b'<title>AutoTasks</title>' in response.data


def test_crud_add(test_app, test_api):
    """Test add a new task

    ## I'm not really sure I should be getting this directly with test_api
    ## But how do I get the number of autotasks from the app endpoint?

    Expected: Both create an autotask AND run it
    """
    data = {
        'name': 'AutoTask 1',
        'category': TaskCategory.Chore.value,
        'priority': 10,
        'notes': 'Description 1',
        'frequency': TaskFrequency.Weekly.value,
        'method': 'add',
    }
    response = test_app.post('/autotasks/crud/', data=data, follow_redirects=True)
    assert response.status_code == 200, show_status_and_response(response)
    assert len(response.history) == 1
    assert response.request.path == '/autotasks/'
    assert b'<title>AutoTasks</title>' in response.data

    # Expect that the autotask ran so it should have inserted the task into tasks table
    tasks_response = test_api.get('/tasks/')
    assert response.status_code == 200, show_status_and_response(tasks_response)
    assert len(tasks_response.json()) == 4


def test_crud_delete(test_app):
    """Test delete a task"""
    data = {
        'id': 1,
        'method': 'delete',
    }
    response = test_app.post('/autotasks/crud/', data=data, follow_redirects=True)
    assert response.status_code == 200, show_status_and_response(response)
    assert len(response.history) == 1
    assert response.request.path == '/autotasks/'
    assert b'<title>AutoTasks</title>' in response.data
