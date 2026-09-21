"""`start_date`/`end_date` on the collection reads whose rows carry a date.

One contract across five endpoints, which is why this is one file rather than
five additions: the semantics have to be identical or the shared `--start`/`--end`
flag names lie. Both bounds are inclusive, either narrows without the other, an
unparsable value is a 422 rather than a silently dropped filter, and a row whose
date is null is outside every range.

`/habits/completed/` is where those semantics come from, and it runs through the
same helper as the rest.

A day is a day on every one of them. `--start X --end X` answers with what is
dated on X whether the column stores a date or an instant. Each class below
asserts that for its own column, because the two types take different branches
and only one of them ever worked.
"""

from datetime import UTC
from datetime import date
from datetime import datetime

import pytest
import sqlalchemy as sa
from fastapi import status
from fastapi.routing import APIRoute

from ichrisbirch import models
from ichrisbirch.api.request_zone import request_zone
from tests.util import show_status_and_response

ARTICLES_ENDPOINT = '/articles/'
BOOKS_ENDPOINT = '/books/'
TASKS_ENDPOINT = '/tasks/'
PROJECT_ITEMS_ENDPOINT = '/project-items/'
PROJECTS_ENDPOINT = '/projects/'
HABITS_COMPLETED_ENDPOINT = '/habits/completed/'


def titles(response) -> set[str]:
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    return {row['title'] for row in response.json()}


class TestArticleReadDateBounds:
    """GET /articles/ bounds on `last_read_date`."""

    @pytest.fixture
    def client_with_read_dates(self, txn_api_logged_in):
        client, session = txn_api_logged_in
        session.add_all(
            [
                models.Article(
                    title=title,
                    url=f'http://example.com/{title}',
                    tags=[],
                    summary=f'{title} summary',
                    save_date=datetime(2026, 1, 1),
                    last_read_date=last_read,
                    read_count=1 if last_read else 0,
                    is_favorite=False,
                    is_current=False,
                    is_archived=False,
                )
                for title, last_read in (
                    ('read in june', datetime(2026, 6, 15, 12)),
                    ('read in july', datetime(2026, 7, 15, 12)),
                    ('read in august', datetime(2026, 8, 15, 12)),
                    ('never read', None),
                )
            ]
        )
        session.flush()
        return client

    def test_unbounded_returns_everything(self, client_with_read_dates):
        assert titles(client_with_read_dates.get(ARTICLES_ENDPOINT)) == {
            'read in june',
            'read in july',
            'read in august',
            'never read',
        }

    def test_start_alone_is_an_open_ended_range(self, client_with_read_dates):
        response = client_with_read_dates.get(ARTICLES_ENDPOINT, params={'start_date': '2026-07-01'})
        assert titles(response) == {'read in july', 'read in august'}

    def test_end_alone_is_an_open_ended_range(self, client_with_read_dates):
        response = client_with_read_dates.get(ARTICLES_ENDPOINT, params={'end_date': '2026-07-01'})
        assert titles(response) == {'read in june'}

    def test_both_bound_a_window(self, client_with_read_dates):
        response = client_with_read_dates.get(ARTICLES_ENDPOINT, params={'start_date': '2026-07-01', 'end_date': '2026-07-31'})
        assert titles(response) == {'read in july'}

    def test_the_bounds_are_inclusive(self, client_with_read_dates):
        """A bound carrying a time keeps the row stamped at it, matching /habits/completed/.

        The test user has no zone, so the time is read in UTC.
        """
        response = client_with_read_dates.get(
            ARTICLES_ENDPOINT,
            params={'start_date': '2026-07-15T12:00:00', 'end_date': '2026-07-15T12:00:00'},
        )
        assert titles(response) == {'read in july'}

    def test_a_single_day_window_finds_the_row_dated_that_day(self, client_with_read_dates):
        """`last_read_date` is a timestamp, and the row is stamped at noon.

        A bare day resolves to the instant it begins, so an inclusive end bound
        would keep only rows stamped exactly midnight and answer with nothing.
        """
        response = client_with_read_dates.get(ARTICLES_ENDPOINT, params={'start_date': '2026-07-15', 'end_date': '2026-07-15'})
        assert titles(response) == {'read in july'}

    def test_a_single_day_window_excludes_the_day_after(self, client_with_read_dates):
        """The widening stops at the next midnight rather than running past it."""
        response = client_with_read_dates.get(ARTICLES_ENDPOINT, params={'start_date': '2026-07-15', 'end_date': '2026-07-16'})
        assert titles(response) == {'read in july'}

    def test_a_never_read_article_is_outside_every_range(self, client_with_read_dates):
        response = client_with_read_dates.get(ARTICLES_ENDPOINT, params={'start_date': '2000-01-01'})
        assert 'never read' not in titles(response)

    def test_the_bounds_compose_with_the_tri_state_filters(self, client_with_read_dates):
        """Two narrowing filters both apply, rather than the last one winning."""
        response = client_with_read_dates.get(ARTICLES_ENDPOINT, params={'unread': 'false', 'start_date': '2026-08-01'})
        assert titles(response) == {'read in august'}

    def test_an_unparsable_bound_is_a_422(self, client_with_read_dates):
        """An empty list would read as a real answer to a question nobody asked."""
        response = client_with_read_dates.get(ARTICLES_ENDPOINT, params={'start_date': 'last tuesday'})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)
        assert 'date' in response.json()['detail'].lower()


class TestBookFinishDateBounds:
    """GET /books/ bounds on `read_finish_date`."""

    @pytest.fixture
    def client_with_finish_dates(self, txn_api_logged_in):
        client, session = txn_api_logged_in
        session.add_all(
            [
                models.Book(title=title, author='A. Writer', tags=[], priority=index, read_finish_date=finished)
                for index, (title, finished) in enumerate(
                    (
                        ('finished in june', datetime(2026, 6, 15, 12)),
                        ('finished in august', datetime(2026, 8, 15, 12)),
                        ('still reading', None),
                    )
                )
            ]
        )
        session.flush()
        return client

    def test_unbounded_returns_everything(self, client_with_finish_dates):
        assert titles(client_with_finish_dates.get(BOOKS_ENDPOINT)) == {
            'finished in june',
            'finished in august',
            'still reading',
        }

    def test_a_window_narrows_to_what_was_finished_in_it(self, client_with_finish_dates):
        response = client_with_finish_dates.get(BOOKS_ENDPOINT, params={'start_date': '2026-08-01', 'end_date': '2026-08-31'})
        assert titles(response) == {'finished in august'}

    def test_a_single_day_window_finds_the_book_finished_that_day(self, client_with_finish_dates):
        """`read_finish_date` is a `Date`, so this is the branch that already worked.

        It is asserted anyway, because the point of the fix is that the answer
        stops depending on which type the column happens to be.
        """
        response = client_with_finish_dates.get(BOOKS_ENDPOINT, params={'start_date': '2026-08-15', 'end_date': '2026-08-15'})
        assert titles(response) == {'finished in august'}

    def test_an_unfinished_book_is_outside_every_range(self, client_with_finish_dates):
        response = client_with_finish_dates.get(BOOKS_ENDPOINT, params={'start_date': '2000-01-01'})
        assert 'still reading' not in titles(response)

    def test_an_unparsable_bound_is_a_422(self, client_with_finish_dates):
        response = client_with_finish_dates.get(BOOKS_ENDPOINT, params={'end_date': 'whenever'})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)


class TestTaskCompleteDateBounds:
    """GET /tasks/ bounds on `complete_date`.

    The bounds live on this endpoint rather than only on `/tasks/completed/`
    because this is the read the CLI makes: `/tasks/completed/` answers a
    different response model and ignores `limit`, so routing a bounded question
    there would change what the caller got back.
    """

    @pytest.fixture
    def client_with_completed_tasks(self, txn_api_logged_in):
        client, session = txn_api_logged_in
        session.add_all(
            [
                models.Task(
                    name=name,
                    category='Chore',
                    priority=index + 1,
                    add_date=datetime(2026, 1, 1),
                    complete_date=completed,
                )
                for index, (name, completed) in enumerate(
                    (
                        ('done in june', datetime(2026, 6, 15, 12)),
                        ('done in august', datetime(2026, 8, 15, 12)),
                        ('still open', None),
                    )
                )
            ]
        )
        session.flush()
        return client

    def names(self, response) -> set[str]:
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        return {row['name'] for row in response.json()}

    def test_the_default_read_is_unchanged_by_the_new_parameters(self, client_with_completed_tasks):
        assert self.names(client_with_completed_tasks.get(TASKS_ENDPOINT)) == {'still open'}

    def test_a_window_narrows_the_completed_read(self, client_with_completed_tasks):
        response = client_with_completed_tasks.get(TASKS_ENDPOINT, params={'status': 'completed', 'start_date': '2026-08-01'})
        assert self.names(response) == {'done in august'}

    def test_a_single_day_window_finds_the_task_completed_that_day(self, client_with_completed_tasks):
        response = client_with_completed_tasks.get(
            TASKS_ENDPOINT,
            params={'status': 'completed', 'start_date': '2026-08-15', 'end_date': '2026-08-15'},
        )
        assert self.names(response) == {'done in august'}

    def test_the_completed_read_takes_the_same_single_day_window(self, client_with_completed_tasks):
        """`/tasks/completed/` carried its own copy of the bounds and its own defect.

        Nothing in this fleet calls it, so it is fixed by folding rather than by
        being found: another client reaching for it gets what the CLI gets.
        """
        response = client_with_completed_tasks.get(
            f'{TASKS_ENDPOINT}completed/',
            params={'start_date': '2026-08-15', 'end_date': '2026-08-15'},
        )
        assert self.names(response) == {'done in august'}

    def test_an_open_task_is_outside_every_range(self, client_with_completed_tasks):
        response = client_with_completed_tasks.get(TASKS_ENDPOINT, params={'status': 'all', 'start_date': '2000-01-01'})
        assert self.names(response) == {'done in june', 'done in august'}

    def test_the_bounds_compose_with_limit(self, client_with_completed_tasks):
        response = client_with_completed_tasks.get(TASKS_ENDPOINT, params={'status': 'completed', 'start_date': '2000-01-01', 'limit': 1})
        assert len(response.json()) == 1, 'limit still caps a bounded read'

    def test_an_unparsable_bound_is_a_422(self, client_with_completed_tasks):
        response = client_with_completed_tasks.get(TASKS_ENDPOINT, params={'start_date': 'yesterday-ish'})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)


class TestTheRequestZoneDecidesTheDay:
    """A task finished at 21:00 in New York on the 20th is 01:00 on the 21st in UTC."""

    @pytest.fixture
    def client_with_an_evening_task(self, txn_api_logged_in):
        client, session = txn_api_logged_in
        session.add(
            models.Task(
                name='done in the evening',
                category='Chore',
                priority=1,
                add_date=datetime(2026, 8, 1, tzinfo=UTC),
                complete_date=datetime(2026, 8, 21, 1, tzinfo=UTC),
            )
        )
        session.flush()
        return client

    def names_on(self, client, day: str, **params) -> set[str]:
        response = client.get(TASKS_ENDPOINT, params={'status': 'completed', 'start_date': day, 'end_date': day, **params})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        return {row['name'] for row in response.json()}

    def test_a_named_zone_puts_the_task_on_its_local_day(self, client_with_an_evening_task):
        assert self.names_on(client_with_an_evening_task, '2026-08-20', timezone='America/New_York') == {'done in the evening'}
        assert self.names_on(client_with_an_evening_task, '2026-08-21', timezone='America/New_York') == set()

    def test_a_user_with_no_preference_reads_utc_days(self, client_with_an_evening_task):
        assert self.names_on(client_with_an_evening_task, '2026-08-21') == {'done in the evening'}

    def test_a_time_with_no_offset_is_read_on_the_named_zones_clock(self, client_with_an_evening_task):
        """20:00 to 23:59 in New York holds the 21:00 task; the same hours in UTC do not."""
        window = {'status': 'completed', 'start_date': '2026-08-20T20:00:00', 'end_date': '2026-08-20T23:59:00'}

        in_new_york = client_with_an_evening_task.get(TASKS_ENDPOINT, params={**window, 'timezone': 'America/New_York'})
        in_utc = client_with_an_evening_task.get(TASKS_ENDPOINT, params=window)

        assert {row['name'] for row in in_new_york.json()} == {'done in the evening'}
        assert {row['name'] for row in in_utc.json()} == set()

    def test_an_unknown_zone_is_a_422_naming_it(self, client_with_an_evening_task):
        response = client_with_an_evening_task.get(TASKS_ENDPOINT, params={'timezone': 'Not/AZone'})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)
        assert 'Not/AZone' in response.text


class TestProjectItemCompletedAtBounds:
    """GET /project-items/ and /projects/{id}/items/ bound on `completed_at`.

    A scope selects which rows come back, never what a filter means, so both
    paths take the same two parameters against the same column.
    """

    @pytest.fixture
    def seeded(self, txn_api_logged_in):
        client, session = txn_api_logged_in
        project = client.post(PROJECTS_ENDPOINT, json={'name': 'Bounded reads'})
        assert project.status_code == status.HTTP_201_CREATED, show_status_and_response(project)
        project_id = project.json()['id']

        created = {}
        for title in ('finished today', 'never finished'):
            response = client.post(PROJECT_ITEMS_ENDPOINT, json={'title': title, 'project_ids': [project_id]})
            assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
            created[title] = response.json()['id']

        completed = client.patch(f'{PROJECT_ITEMS_ENDPOINT}{created["finished today"]}/', json={'completed': True})
        assert completed.status_code == status.HTTP_200_OK, show_status_and_response(completed)
        return client, project_id

    def test_a_window_around_now_finds_what_was_just_finished(self, seeded):
        client, _ = seeded
        response = client.get(PROJECT_ITEMS_ENDPOINT, params={'status': 'completed', 'start_date': '2000-01-01'})
        assert titles(response) == {'finished today'}

    def test_a_window_before_the_completion_finds_nothing(self, seeded):
        client, _ = seeded
        response = client.get(PROJECT_ITEMS_ENDPOINT, params={'status': 'completed', 'end_date': '2000-01-01'})
        assert titles(response) == set()

    def test_todays_single_day_window_finds_what_was_finished_this_minute(self, seeded):
        """The item is stamped now, so the end bound has to reach the rest of today.

        This is the case that sent the CLI looking: a day asked for as a day
        answered with nothing whenever the work happened after midnight.
        """
        client, _ = seeded
        today = datetime.now(UTC).date().isoformat()
        response = client.get(
            PROJECT_ITEMS_ENDPOINT,
            params={'status': 'completed', 'start_date': today, 'end_date': today},
        )
        assert titles(response) == {'finished today'}

    def test_an_item_that_was_never_finished_is_outside_every_range(self, seeded):
        client, _ = seeded
        response = client.get(PROJECT_ITEMS_ENDPOINT, params={'status': 'all', 'start_date': '2000-01-01'})
        assert 'never finished' not in titles(response)

    def test_the_project_scoped_list_takes_the_same_bounds(self, seeded):
        client, project_id = seeded
        response = client.get(f'{PROJECTS_ENDPOINT}{project_id}/items/', params={'status': 'completed', 'start_date': '2000-01-01'})
        assert titles(response) == {'finished today'}

    def test_the_bounds_compose_with_repo(self, seeded):
        client, _ = seeded
        response = client.get(PROJECT_ITEMS_ENDPOINT, params={'status': 'all', 'repo': 'dotfiles', 'start_date': '2000-01-01'})
        assert titles(response) == set()

    def test_an_unparsable_bound_is_a_422(self, seeded):
        client, _ = seeded
        response = client.get(PROJECT_ITEMS_ENDPOINT, params={'start_date': 'this week'})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)


class TestHabitCompleteDateBounds:
    """GET /habits/completed/ bounds on `complete_date`.

    This endpoint wrote the contract and kept its own copy of the comparison,
    which is how it ended up with the defect the contract was meant to prevent.
    It reads through the shared helper now.
    """

    @pytest.fixture
    def client_with_completions(self, txn_api_logged_in):
        client, session = txn_api_logged_in
        category = models.HabitCategory(name='Bounded reads', is_current=True)
        session.add(category)
        session.flush()
        session.add_all(
            [
                models.HabitCompleted(name=name, category_id=category.id, complete_date=done)
                for name, done in (
                    ('done in june', date(2026, 6, 15)),
                    ('done in august', date(2026, 8, 15)),
                )
            ]
        )
        session.flush()
        return client

    def names(self, response) -> set[str]:
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        return {row['name'] for row in response.json()}

    def test_a_single_day_window_finds_the_completion_on_that_day(self, client_with_completions):
        response = client_with_completions.get(
            HABITS_COMPLETED_ENDPOINT,
            params={'start_date': '2026-08-15', 'end_date': '2026-08-15'},
        )
        assert self.names(response) == {'done in august'}

    def test_a_completion_answers_as_a_bare_day(self, client_with_completions):
        """Sent as `2026-08-15T00:00:00Z`, the day would render as the 14th anywhere west of UTC."""
        response = client_with_completions.get(HABITS_COMPLETED_ENDPOINT, params={'start_date': '2026-08-01'})

        assert [row['complete_date'] for row in response.json()] == ['2026-08-15']

    def test_a_bound_carrying_a_time_narrows_by_its_day(self, client_with_completions):
        """The column holds days, so the time on a bound has nothing to compare against."""
        response = client_with_completions.get(
            HABITS_COMPLETED_ENDPOINT,
            params={'start_date': '2026-06-01', 'end_date': '2026-08-15T00:00:00Z'},
        )
        assert self.names(response) == {'done in june', 'done in august'}

    def test_either_bound_still_narrows_on_its_own(self, client_with_completions):
        response = client_with_completions.get(HABITS_COMPLETED_ENDPOINT, params={'start_date': '2026-07-01'})
        assert self.names(response) == {'done in august'}

    def test_an_unparsable_bound_is_still_a_422(self, client_with_completions):
        response = client_with_completions.get(HABITS_COMPLETED_ENDPOINT, params={'start_date': 'not-a-date'})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)


class TestTheBoundsAreAdditive:
    """Every one of these reads answers exactly as before when no bound is passed.

    The point of the parameters is that they are absent by default: a caller who
    does not ask for a range gets the response they got before the parameters
    existed, on every one of the four endpoints.
    """

    @pytest.fixture
    def client_with_rows(self, txn_api_logged_in):
        client, session = txn_api_logged_in
        session.add(
            models.Article(
                title='an article',
                url='http://example.com/a',
                tags=[],
                summary='s',
                save_date=datetime(2026, 1, 1),
                last_read_date=datetime(2026, 6, 1),
                read_count=1,
                is_favorite=False,
                is_current=False,
                is_archived=False,
            )
        )
        session.add(models.Book(title='a book', author='A. Writer', tags=[], priority=1))
        session.add(models.Task(name='a task', category='Chore', priority=1, add_date=datetime(2026, 1, 1)))
        session.flush()
        return client

    @pytest.mark.parametrize('endpoint', [ARTICLES_ENDPOINT, BOOKS_ENDPOINT, TASKS_ENDPOINT, PROJECT_ITEMS_ENDPOINT])
    def test_omitting_the_bounds_matches_sending_them_empty_of_meaning(self, client_with_rows, endpoint):
        bare = client_with_rows.get(endpoint)
        assert bare.status_code == status.HTTP_200_OK, show_status_and_response(bare)

        wide_open = client_with_rows.get(endpoint, params={'start_date': '1900-01-01'})
        assert wide_open.status_code == status.HTTP_200_OK, show_status_and_response(wide_open)
        assert len(wide_open.json()) <= len(bare.json()), 'a bound may only narrow'


# The bounded reads over a `Date` column, which holds a calendar day already and
# takes no zone. Every other bounded read declares `RequestZone`.
DAY_COLUMN_READS = {
    BOOKS_ENDPOINT: models.Book.read_finish_date,
    HABITS_COMPLETED_ENDPOINT: models.HabitCompleted.complete_date,
}


def bounded_reads(api) -> dict[str, APIRoute]:
    """Every GET route taking `start_date` or `end_date`, read off the app rather than listed."""
    found: dict[str, APIRoute] = {}
    for route in api.routes:
        if not isinstance(route, APIRoute) or 'GET' not in route.methods:
            continue
        if {param.name for param in route.dependant.query_params} & {'start_date', 'end_date'}:
            found[route.path] = route
    return found


def declares_request_zone(dependant) -> bool:
    return any(dependency.call is request_zone or declares_request_zone(dependency) for dependency in dependant.dependencies)


def test_every_bounded_read_over_an_instant_column_takes_the_request_zone(txn_api_logged_in):
    """`timezone=None` type-checks whatever the column.

    A new read copied from `/books/` onto a timestamp column passes mypy, then
    answers its first bare day with a 500 from `apply_date_bounds`.
    """
    reads = bounded_reads(txn_api_logged_in[0].app)
    assert {ARTICLES_ENDPOINT, BOOKS_ENDPOINT, TASKS_ENDPOINT, PROJECT_ITEMS_ENDPOINT} <= reads.keys()

    zoneless = {path for path, route in reads.items() if not declares_request_zone(route.dependant)}

    assert zoneless - DAY_COLUMN_READS.keys() == set(), 'bounded reads over an instant column that take no zone'


def test_every_read_exempted_from_the_zone_bounds_a_date_column(txn_api_logged_in):
    assert DAY_COLUMN_READS.keys() <= bounded_reads(txn_api_logged_in[0].app).keys()
    for path, column in DAY_COLUMN_READS.items():
        assert isinstance(column.type, sa.Date), path
        assert not isinstance(column.type, sa.DateTime), path
