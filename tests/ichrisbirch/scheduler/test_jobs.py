import pytest
from freezegun import freeze_time

import tests.util
from ichrisbirch import schemas
from ichrisbirch.models.autotask import AutoTaskFrequency
from ichrisbirch.models.task import TaskCategory
from ichrisbirch.scheduler import jobs
from tests.util import SessionTesting
from tests.util import show_status_and_response


@pytest.fixture(autouse=True)
def insert_testing_data():
    tests.util.insert_test_data('tasks')
    tests.util.insert_test_data('autotasks')
    yield
    tests.util.delete_test_data('tasks')
    tests.util.delete_test_data('autotasks')


def test_decrease_task_priority(test_api_logged_in):
    """Test if able to decrease priority of all tasks."""
    before = test_api_logged_in.get('/tasks/')
    assert before.status_code == 200, show_status_and_response(before)
    assert sum([task['priority'] for task in before.json()]) == 5 + 10 + 15
    jobs.decrease_task_priority(session=SessionTesting)
    after = test_api_logged_in.get('/tasks/')
    assert after.status_code == 200, show_status_and_response(after)
    # Task 3 is completed so it's priority should not be decreased from 15
    assert sum([task['priority'] for task in after.json()]) == 4 + 9 + 15, after.json()
    assert len(before.json()) == len(after.json())


NEW_AUTOTASK = schemas.AutoTaskCreate(
    name='Autotask with too many concurrent tasks',
    notes='Notes for concurrent task',
    category=TaskCategory.Computer,
    priority=3,
    frequency=AutoTaskFrequency.Biweekly,
    max_concurrent=2,
)


def test_check_and_run_autotasks(test_api_logged_in):
    """Test if able to check for autotasks to run."""
    before = test_api_logged_in.get('/tasks/')
    assert before.status_code == 200, show_status_and_response(before)
    assert len(before.json()) == 3
    jobs.check_and_run_autotasks(session=SessionTesting)
    after = test_api_logged_in.get('/tasks/')
    assert after.status_code == 200, show_status_and_response(after)
    assert len(after.json()) == 6, after.json()


def test_check_and_run_autotasks_max_concurrent(test_api_logged_in):
    """Test if auto task with max_concurrent is respected."""
    before = test_api_logged_in.get('/tasks/')
    assert before.status_code == 200, show_status_and_response(before)
    assert len(before.json()) == 3
    # insert all base autotasks again, giving all conccurent of 1
    # base data has run dates of 2020
    with freeze_time('2021-03-20'):
        jobs.check_and_run_autotasks(session=SessionTesting)
        add_tasks = test_api_logged_in.get('/tasks/')
        assert add_tasks.status_code == 200, show_status_and_response(add_tasks)
        assert len(add_tasks.json()) == 6, add_tasks.json()
    # run autotask check again, giving all conccurent of 2
    with freeze_time('2022-03-20'):
        jobs.check_and_run_autotasks(session=SessionTesting)
        add_tasks_again = test_api_logged_in.get('/tasks/')
        assert add_tasks_again.status_code == 200, show_status_and_response(add_tasks_again)
        assert len(add_tasks_again.json()) == 9, add_tasks_again.json()
    # run autotask check, no new tasks should be added as all are at max_concurrent
    with freeze_time('2023-03-20'):
        jobs.check_and_run_autotasks(session=SessionTesting)
        no_add_tasks = test_api_logged_in.get('/tasks/')
        assert no_add_tasks.status_code == 200, show_status_and_response(no_add_tasks)
        assert len(no_add_tasks.json()) == 9, no_add_tasks.json()
