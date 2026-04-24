import pytest
from freezegun import freeze_time

from ichrisbirch import schemas
from ichrisbirch.scheduler import jobs
from tests.util import show_status_and_response
from tests.utils.database import delete_test_data
from tests.utils.database import insert_test_data
from tests.utils.database import test_settings


@pytest.fixture(autouse=True)
def insert_testing_data():
    insert_test_data('tasks')
    insert_test_data('autotasks')
    yield
    delete_test_data('tasks')
    delete_test_data('autotasks')


def test_compact_task_priorities(test_api_logged_in):
    """Dense-rank incomplete tasks to 1..K; completed tasks are untouched."""
    # Bump incomplete task priorities to non-dense values so the compaction
    # has something to do. The two incomplete tasks start at 1 and 2 per the
    # baseline fixture — push them to 7 and 12 to simulate a post-add_date
    # pile-up that would be tidied up overnight.
    todo = test_api_logged_in.get('/tasks/todo/').json()
    assert len(todo) == 2, todo
    ids_in_order = [t['id'] for t in todo]
    test_api_logged_in.patch(f'/tasks/{ids_in_order[0]}/', json={'priority': 7})
    test_api_logged_in.patch(f'/tasks/{ids_in_order[1]}/', json={'priority': 12})

    jobs.compact_task_priorities(test_settings)

    after = test_api_logged_in.get('/tasks/todo/').json()
    assert [t['priority'] for t in after] == [1, 2], after
    # Same task that was rank-1 by add_date should still be rank-1 afterward.
    assert [t['id'] for t in after] == ids_in_order

    # Completed task's priority is untouched (baseline priority = 3).
    completed = test_api_logged_in.get('/tasks/completed/').json()
    assert len(completed) == 1
    assert completed[0]['priority'] == 3


NEW_AUTOTASK = schemas.AutoTaskCreate(
    name='Autotask with too many concurrent tasks',
    notes='Notes for concurrent task',
    category='Computer',
    priority=3,
    frequency='Biweekly',
    max_concurrent=2,
)


def test_check_and_run_autotasks(test_api_logged_in):
    """Test if able to check for autotasks to run."""
    before = test_api_logged_in.get('/tasks/')
    assert before.status_code == 200, show_status_and_response(before)
    assert len(before.json()) == 3
    jobs.check_and_run_autotasks(test_settings)
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
        jobs.check_and_run_autotasks(test_settings)
        add_tasks = test_api_logged_in.get('/tasks/')
        assert add_tasks.status_code == 200, show_status_and_response(add_tasks)
        assert len(add_tasks.json()) == 6, add_tasks.json()
    # run autotask check again, giving all conccurent of 2
    with freeze_time('2022-03-20'):
        jobs.check_and_run_autotasks(test_settings)
        add_tasks_again = test_api_logged_in.get('/tasks/')
        assert add_tasks_again.status_code == 200, show_status_and_response(add_tasks_again)
        assert len(add_tasks_again.json()) == 9, add_tasks_again.json()
    # run autotask check, no new tasks should be added as all are at max_concurrent
    with freeze_time('2023-03-20'):
        jobs.check_and_run_autotasks(test_settings)
        no_add_tasks = test_api_logged_in.get('/tasks/')
        assert no_add_tasks.status_code == 200, show_status_and_response(no_add_tasks)
        assert len(no_add_tasks.json()) == 9, no_add_tasks.json()
