from tests.helpers import show_status_and_response
from tests.testing_data.autotasks import CREATE_DATA


def test_index(test_app):
    """Test the index page"""
    response = test_app.get('/autotasks/')
    assert response.status_code == 200, show_status_and_response(response)
    assert b'<title>AutoTasks</title>' in response.data


def test_crud_add(test_app, test_api):
    """Test add a new task
    I'm not really sure I should be getting this directly with test_api
    But how do I get the number of autotasks from the app endpoint?
    Expected: Both create an autotask AND run it
    """
    response = test_app.post('/autotasks/crud/', data=CREATE_DATA | {'method': 'add'}, follow_redirects=True)
    assert response.status_code == 200, show_status_and_response(response)
    assert len(response.history) == 1
    assert response.request.path == '/autotasks/'
    assert b'<title>AutoTasks</title>' in response.data

    # Expect that the autotask ran so it should have inserted the task into tasks table
    tasks_response = test_api.get('/tasks/')
    assert response.status_code == 200, show_status_and_response(tasks_response)
    assert len(tasks_response.json()) == 4


def test_crud_delete(test_app):
    response = test_app.post('/autotasks/crud/', data={'id': 1, 'method': 'delete'}, follow_redirects=True)
    assert response.status_code == 200, show_status_and_response(response)
    assert len(response.history) == 1
    assert response.request.path == '/autotasks/'
    assert b'<title>AutoTasks</title>' in response.data
