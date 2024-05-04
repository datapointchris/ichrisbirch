from ichrisbirch.scheduler import jobs
from tests.helpers import show_status_and_response


def test_decrease_task_priority(test_api):
    """Test if able to decrease priority of all tasks"""
    before = test_api.get('/tasks/')
    assert before.status_code == 200, show_status_and_response(before)
    assert sum([task['priority'] for task in before.json()]) == 5 + 10 + 15
    jobs.decrease_task_priority()
    after = test_api.get('/tasks/')
    assert after.status_code == 200, show_status_and_response(after)
    # Task 3 is completed so it's priority should not be decreased from 15
    assert sum([task['priority'] for task in after.json()]) == 4 + 9 + 15
    assert len(before.json()) == len(after.json())


def test_check_and_run_autotasks(test_api):
    """Test if able to check for autotasks to run"""
    before = test_api.get('/tasks/')
    assert before.status_code == 200, show_status_and_response(before)
    assert len(before.json()) == 3
    jobs.check_and_run_autotasks()
    after = test_api.get('/tasks/')
    assert after.status_code == 200, show_status_and_response(after)
    assert len(after.json()) == 6
