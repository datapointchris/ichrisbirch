import pytest
from fastapi import status

from ichrisbirch import schemas
from ichrisbirch.models.task import TASK_CATEGORIES
from tests.util import show_status_and_response
from tests.utils.database import insert_test_data_transactional

from .crud_test import ApiCrudTester

ENDPOINT = '/tasks/'
NEW_OBJ = schemas.TaskCreate(
    name='Task 4 Computer with notes priority 3',
    notes='Notes task 4',
    category='Computer',
    priority=3,
)


@pytest.fixture
def task_crud_tester(txn_api_logged_in):
    """Provide ApiCrudTester with transactional test data."""
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'tasks')
    # status=all because these measure create and delete, not the filter:
    # the list defaults to open, and the seed holds one completed task.
    crud_tester = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ, list_params={'status': 'all'})
    return client, crud_tester


def test_read_one(task_crud_tester):
    client, crud_tester = task_crud_tester
    crud_tester.test_read_one(client)


def test_read_many(task_crud_tester):
    client, crud_tester = task_crud_tester
    crud_tester.test_read_many(client)


def test_create(task_crud_tester):
    client, crud_tester = task_crud_tester
    crud_tester.test_create(client)


def test_delete(task_crud_tester):
    client, crud_tester = task_crud_tester
    crud_tester.test_delete(client)


def test_lifecycle(task_crud_tester):
    client, crud_tester = task_crud_tester
    crud_tester.test_lifecycle(client)


def test_read_many_tasks_completed(task_crud_tester):
    client, _ = task_crud_tester
    response = client.get('/tasks/completed/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 1


def test_read_many_tasks_not_completed(task_crud_tester):
    client, _ = task_crud_tester
    response = client.get(f'{ENDPOINT}todo/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 2


def test_complete_task(task_crud_tester):
    client, crud_tester = task_crud_tester
    first_id = crud_tester.item_id_by_position(client, position=1)
    response = client.patch(f'{ENDPOINT}{first_id}/complete/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


def test_read_completed_tasks(task_crud_tester):
    client, _ = task_crud_tester
    completed = client.get('/tasks/completed/')
    assert completed.status_code == status.HTTP_200_OK, show_status_and_response(completed)
    assert len(completed.json()) == 1


def test_search_task(task_crud_tester):
    client, _ = task_crud_tester
    search_term = 'chore'
    search_results = client.get('/tasks/search/', params={'q': search_term})
    assert search_results.status_code == status.HTTP_200_OK, show_status_and_response(search_results)
    assert len(search_results.json()) == 1

    search_term = 'home'
    search_results = client.get('/tasks/search/', params={'q': search_term})
    assert search_results.status_code == status.HTTP_200_OK, show_status_and_response(search_results)
    assert len(search_results.json()) == 2


@pytest.mark.parametrize('category', TASK_CATEGORIES)
def test_task_categories(txn_api_logged_in, category):
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'tasks')
    test_task = schemas.TaskCreate(
        name='Task 4 Computer with notes priority 3',
        notes='Notes task 4',
        category=category,
        priority=3,
    )
    created_task = client.post(ENDPOINT, json=test_task.model_dump())
    assert created_task.status_code == status.HTTP_201_CREATED, show_status_and_response(created_task)
    assert created_task.json()['name'] == test_task.name


def test_reorder_dense_ranks_incomplete_tasks(task_crud_tester):
    """POST /tasks/reorder/ compacts incomplete priorities to a dense 1..K sequence."""
    client, _ = task_crud_tester
    # Bump the two incomplete tasks to non-dense values so there's something to compact.
    todo = client.get('/tasks/todo/').json()
    ids_in_order = [t['id'] for t in todo]
    client.patch(f'/tasks/{ids_in_order[0]}/', json={'priority': 5})
    client.patch(f'/tasks/{ids_in_order[1]}/', json={'priority': 20})

    # Add a "pin to top" style task at priority 0.
    PINNED_TASK = schemas.TaskCreate(name='Pinned to top', notes=None, category='Home', priority=0)
    pinned_response = client.post(ENDPOINT, json=PINNED_TASK.model_dump())
    pinned_id = pinned_response.json()['id']

    response = client.post('/tasks/reorder/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert response.json().get('message') == 'Reordered 3 tasks'

    after = client.get('/tasks/todo/').json()
    # Dense 1..K, tiebreak by add_date ASC. Pinned (priority 0) was lowest so it's rank 1.
    assert [t['priority'] for t in after] == [1, 2, 3]
    assert after[0]['id'] == pinned_id
    assert [t['id'] for t in after[1:]] == ids_in_order


def test_reorder_with_no_incomplete_tasks(txn_api_logged_in):
    """POST /tasks/reorder/ returns a friendly message when there are no incomplete tasks."""
    client, _ = txn_api_logged_in
    response = client.post('/tasks/reorder/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert response.json().get('message') == 'No tasks to reorder'


def test_create_task_without_priority_defaults_to_1(txn_api_logged_in):
    """Omitting priority on TaskCreate should default to 1 (top of the list)."""
    client, _ = txn_api_logged_in
    response = client.post(ENDPOINT, json={'name': 'No explicit priority', 'category': 'Chore'})
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    assert response.json()['priority'] == 1


def test_completed_with_date_filter(task_crud_tester):
    """Test /tasks/completed/ endpoint with date filtering.

    The test data has one completed task with complete_date=2020-04-20.
    This test verifies:
    1. Date range including 2020-04-20 returns the task
    2. Date range excluding 2020-04-20 returns empty list

    This test should FAIL if date strings are not properly parsed to datetime.
    """
    client, _ = task_crud_tester

    # Date range that INCLUDES the completed task (2020-04-20)
    response_with_match = client.get(
        '/tasks/completed/',
        params={
            'start_date': '2020-04-01T00:00:00',
            'end_date': '2020-04-30T23:59:59',
        },
    )
    assert response_with_match.status_code == status.HTTP_200_OK, show_status_and_response(response_with_match)
    assert len(response_with_match.json()) == 1, 'Expected 1 completed task in April 2020 date range'

    # Date range that EXCLUDES the completed task (2020-04-20)
    response_no_match = client.get(
        '/tasks/completed/',
        params={
            'start_date': '2025-01-01T00:00:00',
            'end_date': '2025-12-31T23:59:59',
        },
    )
    assert response_no_match.status_code == status.HTTP_200_OK, show_status_and_response(response_no_match)
    assert len(response_no_match.json()) == 0, 'Expected 0 completed tasks in 2025 date range'


def test_completed_with_one_bound_is_open_ended(task_crud_tester):
    """One bound narrows on its own; a half-specified range never widens to everything.

    The test data has one completed task with complete_date=2020-04-20.
    """
    client, _ = task_crud_tester

    cases = [
        ({'start_date': '2020-01-01T00:00:00'}, 1),
        ({'start_date': '2025-01-01T00:00:00'}, 0),
        ({'end_date': '2020-12-31T23:59:59'}, 1),
        ({'end_date': '2019-12-31T23:59:59'}, 0),
    ]
    for params, expected in cases:
        response = client.get('/tasks/completed/', params=params)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert len(response.json()) == expected, f'{params} expected {expected} completed tasks'


def test_completed_with_invalid_dates(task_crud_tester):
    """Test /tasks/completed/ endpoint with invalid date formats.

    API should return 422 Unprocessable Entity for malformed dates.
    """
    client, _ = task_crud_tester

    # Invalid date format
    response = client.get(
        '/tasks/completed/',
        params={
            'start_date': 'not-a-date',
            'end_date': '2020-04-30T23:59:59',
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, show_status_and_response(response)


def test_todo_with_limit(task_crud_tester):
    """Test /tasks/todo/ endpoint with limit parameter.

    Test data has 2 uncompleted tasks (priority 1 and 2).
    Limit should restrict the number of results.
    """
    client, _ = task_crud_tester

    # Without limit - should get all 2 uncompleted tasks
    response_all = client.get('/tasks/todo/')
    assert response_all.status_code == status.HTTP_200_OK, show_status_and_response(response_all)
    assert len(response_all.json()) == 2, 'Expected 2 uncompleted tasks without limit'

    # With limit=1 - should get only 1 task (lowest priority first)
    response_limited = client.get('/tasks/todo/', params={'limit': 1})
    assert response_limited.status_code == status.HTTP_200_OK, show_status_and_response(response_limited)
    assert len(response_limited.json()) == 1, 'Expected 1 task with limit=1'

    # The returned task should be the one with lowest priority (1)
    tasks = response_limited.json()
    assert tasks[0]['priority'] == 1, 'Expected task with priority 1 (lowest) to be returned first'


class TestTaskStatusFilter:
    """GET /tasks/?status= — one list that can express every status.

    `/todo/` and `/completed/` answer narrower versions of the same question and
    stay for the web app. The CLI asks this one, so it has to reach every status
    rather than one per path.

    The default narrows to open because completed tasks accumulate without
    bound, per cli-design.md § "A default narrows only where the hidden class
    grows without bound". The seed holds 2 open and 1 completed.
    """

    def names(self, client, params=None):
        response = client.get(ENDPOINT, params=params)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        return response.json()

    def test_the_default_is_open_only(self, task_crud_tester):
        client, _ = task_crud_tester
        tasks = self.names(client)
        assert len(tasks) == 2
        assert all(task['complete_date'] is None for task in tasks)

    def test_completed_returns_the_finished_one(self, task_crud_tester):
        client, _ = task_crud_tester
        tasks = self.names(client, {'status': 'completed'})
        assert len(tasks) == 1
        assert tasks[0]['complete_date'] is not None

    def test_all_returns_every_task(self, task_crud_tester):
        client, _ = task_crud_tester
        assert len(self.names(client, {'status': 'all'})) == 3

    def test_open_and_completed_partition_all(self, task_crud_tester):
        client, _ = task_crud_tester
        ids = {s: {t['id'] for t in self.names(client, {'status': s})} for s in ('open', 'completed')}
        every = {t['id'] for t in self.names(client, {'status': 'all'})}

        assert ids['open'] | ids['completed'] == every
        assert not ids['open'] & ids['completed'], 'a task cannot be both'

    def test_completed_orders_by_when_it_was_finished(self, task_crud_tester):
        """Priority stopped meaning anything the moment the task left the queue."""
        client, _ = task_crud_tester
        tasks = self.names(client, {'status': 'completed'})
        dates = [t['complete_date'] for t in tasks]
        assert dates == sorted(dates, reverse=True)

    def test_an_unknown_status_names_the_known_ones(self, task_crud_tester):
        client, _ = task_crud_tester
        response = client.get(ENDPOINT, params={'status': 'todo'})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, show_status_and_response(response)
        assert 'open' in response.json()['detail'], 'the error must name the word that was meant'

    def test_limit_still_applies(self, task_crud_tester):
        client, _ = task_crud_tester
        assert len(self.names(client, {'status': 'all', 'limit': 1})) == 1
