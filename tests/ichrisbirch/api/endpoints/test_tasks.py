import datetime as dt

import pytest
from fastapi import status

from ichrisbirch import schemas
from ichrisbirch.models.task import TASK_CATEGORIES
from ichrisbirch.models.task import TASK_CATEGORY_WINDOW_DAYS
from tests.util import show_status_and_response
from tests.utils.database import insert_test_data_transactional

from .crud_test import ApiCrudTester

ENDPOINT = '/tasks/'
NEW_OBJ = schemas.TaskCreate(
    name='Task 4 Computer with notes',
    notes='Notes task 4',
    category='Computer',
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
    test_task = schemas.TaskCreate(name='Task 4 Computer with notes', notes='Notes task 4', category=category)
    created_task = client.post(ENDPOINT, json=test_task.model_dump())
    assert created_task.status_code == status.HTTP_201_CREATED, show_status_and_response(created_task)
    assert created_task.json()['window_days'] == TASK_CATEGORY_WINDOW_DAYS[category]


def create(client, **fields):
    response = client.post(ENDPOINT, json={'category': 'Chore', **fields})
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    return response.json()


def todo_ids(client):
    response = client.get(f'{ENDPOINT}todo/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    return [task['id'] for task in response.json()]


class TestQueueOrder:
    """Open tasks read pinned first, then by `rank_at`, then by `add_date`."""

    def test_a_new_task_ranks_its_window_from_now(self, txn_api_logged_in):
        client, _ = txn_api_logged_in
        before = dt.datetime.now(dt.UTC)
        task = create(client, name='Water plants', category='Dingo')

        assert task['window_days'] == TASK_CATEGORY_WINDOW_DAYS['Dingo']
        rank_at = dt.datetime.fromisoformat(task['rank_at'])
        assert before + dt.timedelta(days=7) <= rank_at <= dt.datetime.now(dt.UTC) + dt.timedelta(days=7)

    def test_a_given_window_overrides_the_category(self, txn_api_logged_in):
        client, _ = txn_api_logged_in
        assert create(client, name='Soon', window_days=2)['window_days'] == 2

    def test_a_window_below_one_day_is_refused(self, txn_api_logged_in):
        client, _ = txn_api_logged_in
        response = client.post(ENDPOINT, json={'name': 'Never', 'category': 'Chore', 'window_days': 0})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)

    def test_an_unknown_category_on_create_is_refused(self, txn_api_logged_in):
        client, _ = txn_api_logged_in
        response = client.post(ENDPOINT, json={'name': 'Lost', 'category': 'Hobby'})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)
        assert 'Hobby' in response.json()['detail']

    def test_a_shorter_window_sorts_ahead_of_an_older_longer_one(self, txn_api_logged_in):
        """Research is made first and still sorts last, so a new task does not land on top for being new."""
        client, _ = txn_api_logged_in
        research = create(client, name='Projection mapping', category='Research')
        nails = create(client, name='Trim nails', category='Dingo')
        purchase = create(client, name='Camping mattress', category='Purchase')

        assert todo_ids(client) == [nails['id'], purchase['id'], research['id']]

    def test_a_pinned_task_sorts_first_whatever_its_window(self, txn_api_logged_in):
        client, _ = txn_api_logged_in
        soon = create(client, name='Soon', window_days=1)
        pinned = create(client, name='Pinned', window_days=365, pinned=True)

        assert todo_ids(client) == [pinned['id'], soon['id']]

    def test_pinning_through_an_update_changes_nothing_else(self, txn_api_logged_in):
        client, _ = txn_api_logged_in
        task = create(client, name='Keep me', window_days=12)

        pinned = client.patch(f'{ENDPOINT}{task["id"]}/', json={'pinned': True}).json()
        assert pinned['pinned'] is True
        assert (pinned['name'], pinned['window_days'], pinned['rank_at']) == (task['name'], task['window_days'], task['rank_at'])

    def test_moving_rank_at_reorders_the_list(self, txn_api_logged_in):
        """What a drag in the web app sends: a rank_at between two neighbors."""
        client, _ = txn_api_logged_in
        first = create(client, name='First', window_days=1)
        second = create(client, name='Second', window_days=2)
        third = create(client, name='Third', window_days=3)
        between = (dt.datetime.fromisoformat(first['rank_at']) - dt.timedelta(hours=1)).isoformat()

        response = client.patch(f'{ENDPOINT}{third["id"]}/', json={'rank_at': between})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert todo_ids(client) == [third['id'], first['id'], second['id']]


class TestSnooze:
    def test_snooze_restarts_the_window_from_now(self, txn_api_logged_in):
        client, _ = txn_api_logged_in
        task = create(client, name='Later', window_days=5)
        client.patch(f'{ENDPOINT}{task["id"]}/', json={'rank_at': '2020-01-01T00:00:00+00:00'})

        before = dt.datetime.now(dt.UTC)
        response = client.patch(f'{ENDPOINT}{task["id"]}/snooze/')
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert dt.datetime.fromisoformat(response.json()['rank_at']) >= before + dt.timedelta(days=5)

    def test_snooze_moves_a_task_behind_the_others(self, txn_api_logged_in):
        client, _ = txn_api_logged_in
        first = create(client, name='First', window_days=5)
        second = create(client, name='Second', window_days=1)
        client.patch(f'{ENDPOINT}{first["id"]}/', json={'rank_at': '2020-01-01T00:00:00+00:00'})
        assert todo_ids(client) == [first['id'], second['id']]

        client.patch(f'{ENDPOINT}{first["id"]}/snooze/')
        assert todo_ids(client) == [second['id'], first['id']]

    def test_snooze_unpins(self, txn_api_logged_in):
        client, _ = txn_api_logged_in
        task = create(client, name='Pinned', pinned=True)

        response = client.patch(f'{ENDPOINT}{task["id"]}/snooze/')
        assert response.json()['pinned'] is False

    def test_a_closed_task_cannot_be_snoozed(self, txn_api_logged_in):
        client, _ = txn_api_logged_in
        task = create(client, name='Done')
        client.patch(f'{ENDPOINT}{task["id"]}/complete/')

        response = client.patch(f'{ENDPOINT}{task["id"]}/snooze/')
        assert response.status_code == status.HTTP_409_CONFLICT, show_status_and_response(response)


class TestDrop:
    def test_a_dropped_task_leaves_the_open_list_and_keeps_its_reason(self, txn_api_logged_in):
        client, _ = txn_api_logged_in
        task = create(client, name='Learn the theremin')

        response = client.patch(f'{ENDPOINT}{task["id"]}/drop/', json={'reason': 'Lost interest'})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json()['drop_date'] is not None
        assert response.json()['drop_reason'] == 'Lost interest'
        assert task['id'] not in todo_ids(client)

    def test_a_reason_is_optional(self, txn_api_logged_in):
        client, _ = txn_api_logged_in
        task = create(client, name='Whatever')

        response = client.patch(f'{ENDPOINT}{task["id"]}/drop/')
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json()['drop_reason'] is None

    def test_dropped_is_its_own_status_and_not_completed(self, txn_api_logged_in):
        client, _ = txn_api_logged_in
        dropped = create(client, name='Dropped')
        completed = create(client, name='Completed')
        client.patch(f'{ENDPOINT}{dropped["id"]}/drop/')
        client.patch(f'{ENDPOINT}{completed["id"]}/complete/')

        assert [t['id'] for t in client.get(ENDPOINT, params={'status': 'dropped'}).json()] == [dropped['id']]
        assert [t['id'] for t in client.get(ENDPOINT, params={'status': 'completed'}).json()] == [completed['id']]
        assert [t['id'] for t in client.get(f'{ENDPOINT}completed/').json()] == [completed['id']]

    def test_a_completed_task_cannot_be_dropped(self, txn_api_logged_in):
        client, _ = txn_api_logged_in
        task = create(client, name='Done')
        client.patch(f'{ENDPOINT}{task["id"]}/complete/')

        response = client.patch(f'{ENDPOINT}{task["id"]}/drop/')
        assert response.status_code == status.HTTP_409_CONFLICT, show_status_and_response(response)
        assert 'completed' in response.json()['detail']

    def test_a_dropped_task_cannot_be_completed(self, txn_api_logged_in):
        client, _ = txn_api_logged_in
        task = create(client, name='Let go')
        client.patch(f'{ENDPOINT}{task["id"]}/drop/')

        response = client.patch(f'{ENDPOINT}{task["id"]}/complete/')
        assert response.status_code == status.HTTP_409_CONFLICT, show_status_and_response(response)

    def test_an_update_cannot_set_both_closed_dates(self, txn_api_logged_in):
        client, _ = txn_api_logged_in
        task = create(client, name='Both')
        client.patch(f'{ENDPOINT}{task["id"]}/drop/')

        response = client.patch(f'{ENDPOINT}{task["id"]}/', json={'complete_date': '2026-10-01T12:00:00+00:00'})
        assert response.status_code == status.HTTP_409_CONFLICT, show_status_and_response(response)


class TestReopen:
    @pytest.mark.parametrize('verb', ['drop', 'complete'])
    def test_a_closed_task_returns_to_the_list_at_its_rank(self, txn_api_logged_in, verb):
        client, _ = txn_api_logged_in
        task = create(client, name='Back again')
        client.patch(f'{ENDPOINT}{task["id"]}/{verb}/')

        response = client.patch(f'{ENDPOINT}{task["id"]}/reopen/')
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json()['complete_date'] is None
        assert response.json()['drop_date'] is None
        assert response.json()['rank_at'] == task['rank_at']
        assert task['id'] in todo_ids(client)

    def test_reopening_a_dropped_task_clears_its_reason(self, txn_api_logged_in):
        client, _ = txn_api_logged_in
        task = create(client, name='Meh')
        client.patch(f'{ENDPOINT}{task["id"]}/drop/', json={'reason': 'meh'})

        assert client.patch(f'{ENDPOINT}{task["id"]}/reopen/').json()['drop_reason'] is None

    def test_an_open_task_cannot_be_reopened(self, txn_api_logged_in):
        client, _ = txn_api_logged_in
        task = create(client, name='Open')

        response = client.patch(f'{ENDPOINT}{task["id"]}/reopen/')
        assert response.status_code == status.HTTP_409_CONFLICT, show_status_and_response(response)
        assert 'already open' in response.json()['detail']


class TestClosedState:
    """Only an open task is pinned, and only a dropped task has a reason, by every route."""

    @pytest.mark.parametrize('verb', ['drop', 'complete'])
    def test_closing_a_pinned_task_unpins_it(self, txn_api_logged_in, verb):
        client, _ = txn_api_logged_in
        task = create(client, name='Pinned', pinned=True)

        response = client.patch(f'{ENDPOINT}{task["id"]}/{verb}/')
        assert response.json()['pinned'] is False

    def test_closing_through_an_update_unpins(self, txn_api_logged_in):
        client, _ = txn_api_logged_in
        task = create(client, name='Pinned', pinned=True)

        response = client.patch(f'{ENDPOINT}{task["id"]}/', json={'complete_date': '2026-10-01T12:00:00+00:00'})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json()['pinned'] is False

    @pytest.mark.parametrize('verb', ['drop', 'complete'])
    def test_a_closed_task_cannot_be_pinned(self, txn_api_logged_in, verb):
        client, _ = txn_api_logged_in
        task = create(client, name='Closed')
        client.patch(f'{ENDPOINT}{task["id"]}/{verb}/')

        response = client.patch(f'{ENDPOINT}{task["id"]}/', json={'pinned': True})
        assert response.status_code == status.HTTP_409_CONFLICT, show_status_and_response(response)
        assert client.get(f'{ENDPOINT}{task["id"]}/').json()['pinned'] is False

    def test_clearing_the_drop_date_clears_the_reason(self, txn_api_logged_in):
        client, _ = txn_api_logged_in
        task = create(client, name='Back again')
        client.patch(f'{ENDPOINT}{task["id"]}/drop/', json={'reason': 'meh'})

        response = client.patch(f'{ENDPOINT}{task["id"]}/', json={'drop_date': None})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json()['drop_reason'] is None
        assert task['id'] in todo_ids(client)

    def test_an_open_task_cannot_be_given_a_drop_reason(self, txn_api_logged_in):
        client, _ = txn_api_logged_in
        task = create(client, name='Open')

        response = client.patch(f'{ENDPOINT}{task["id"]}/', json={'drop_reason': 'meh'})
        assert response.status_code == status.HTTP_409_CONFLICT, show_status_and_response(response)


class TestCategoryWindows:
    def test_every_category_is_listed_with_its_window(self, txn_api_logged_in):
        client, _ = txn_api_logged_in
        response = client.get(f'{ENDPOINT}categories/')
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert {c['name']: c['window_days'] for c in response.json()} == TASK_CATEGORY_WINDOW_DAYS

    def test_a_changed_window_applies_to_the_next_task(self, txn_api_logged_in):
        client, _ = txn_api_logged_in
        response = client.patch(f'{ENDPOINT}categories/Home/', json={'window_days': 12})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)

        assert create(client, name='Fix the fence', category='Home')['window_days'] == 12

    def test_an_unknown_category_is_not_found(self, txn_api_logged_in):
        client, _ = txn_api_logged_in
        response = client.patch(f'{ENDPOINT}categories/Hobby/', json={'window_days': 12})
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_a_window_below_one_day_is_refused(self, txn_api_logged_in):
        client, _ = txn_api_logged_in
        response = client.patch(f'{ENDPOINT}categories/Home/', json={'window_days': 0})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)


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
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)


def test_todo_with_limit(task_crud_tester):
    """Test /tasks/todo/ endpoint with limit parameter.

    Test data has 2 uncompleted tasks, the Chore one ranked first.
    Limit should restrict the number of results.
    """
    client, _ = task_crud_tester

    response_all = client.get('/tasks/todo/')
    assert response_all.status_code == status.HTTP_200_OK, show_status_and_response(response_all)
    assert len(response_all.json()) == 2, 'Expected 2 uncompleted tasks without limit'

    response_limited = client.get('/tasks/todo/', params={'limit': 1})
    assert response_limited.status_code == status.HTTP_200_OK, show_status_and_response(response_limited)
    assert len(response_limited.json()) == 1, 'Expected 1 task with limit=1'
    assert response_limited.json()[0]['category'] == 'Chore', 'Expected the earliest-ranked task first'


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
        client, _ = task_crud_tester
        tasks = self.names(client, {'status': 'completed'})
        dates = [t['complete_date'] for t in tasks]
        assert dates == sorted(dates, reverse=True)

    def test_an_unknown_status_names_the_known_ones(self, task_crud_tester):
        client, _ = task_crud_tester
        response = client.get(ENDPOINT, params={'status': 'todo'})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)
        assert 'open' in response.json()['detail'], 'the error must name the word that was meant'

    def test_limit_still_applies(self, task_crud_tester):
        client, _ = task_crud_tester
        assert len(self.names(client, {'status': 'all', 'limit': 1})) == 1

    def test_a_category_narrows_to_that_category(self, task_crud_tester):
        """The seed holds one Chore and two Home, one of the Home ones done."""
        client, _ = task_crud_tester
        tasks = self.names(client, {'category': 'Home'})

        assert [task['category'] for task in tasks] == ['Home']

    def test_a_category_composes_with_the_status(self, task_crud_tester):
        client, _ = task_crud_tester

        assert len(self.names(client, {'category': 'Home', 'status': 'all'})) == 2
        assert len(self.names(client, {'category': 'Chore', 'status': 'all'})) == 1

    def test_limit_caps_the_category_rather_than_the_whole_list(self, task_crud_tester):
        """The property `cli-design.md` § "Filtering is server-side" is about: a
        caller filtering after the fact would have limit cap the wrong set, and
        get back nothing while rows it asked for sat past the cap."""
        client, _ = task_crud_tester
        tasks = self.names(client, {'category': 'Home', 'status': 'all', 'limit': 1})

        assert len(tasks) == 1
        assert tasks[0]['category'] == 'Home'

    def test_a_known_category_with_nothing_in_it_is_empty_not_an_error(self, task_crud_tester):
        client, _ = task_crud_tester

        assert self.names(client, {'category': 'Learn', 'status': 'all'}) == []

    def test_an_unknown_category_names_the_known_ones(self, task_crud_tester):
        client, _ = task_crud_tester
        response = client.get(ENDPOINT, params={'category': 'Hobby'})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)
        assert 'Personal' in response.json()['detail'], 'the error must name the word that was meant'

    def test_omitting_the_category_lists_every_one(self, task_crud_tester):
        client, _ = task_crud_tester

        assert len(self.names(client, {'status': 'all'})) == 3
