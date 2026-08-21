"""`start_date`/`end_date` on the collection reads whose rows carry a date.

One contract across four endpoints, which is why this is one file rather than
four additions: the semantics have to be identical or the shared `--start`/`--end`
flag names lie. Both bounds are inclusive, either narrows without the other, an
unparsable value is a 422 rather than a silently dropped filter, and a row whose
date is null is outside every range.

`/habits/completed/` is where those semantics come from. It is deliberately not
folded into the shared helper here: it answers its own callers today and moving
it would change them.
"""

from datetime import datetime

import pytest
from fastapi import status

from ichrisbirch import models
from tests.util import show_status_and_response

ARTICLES_ENDPOINT = '/articles/'
BOOKS_ENDPOINT = '/books/'
TASKS_ENDPOINT = '/tasks/'
PROJECT_ITEMS_ENDPOINT = '/project-items/'
PROJECTS_ENDPOINT = '/projects/'


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
        """An exact-instant bound keeps the row it names, matching /habits/completed/."""
        response = client_with_read_dates.get(
            ARTICLES_ENDPOINT,
            params={'start_date': '2026-07-15T12:00:00', 'end_date': '2026-07-15T12:00:00'},
        )
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

    def test_an_open_task_is_outside_every_range(self, client_with_completed_tasks):
        response = client_with_completed_tasks.get(TASKS_ENDPOINT, params={'status': 'all', 'start_date': '2000-01-01'})
        assert self.names(response) == {'done in june', 'done in august'}

    def test_the_bounds_compose_with_limit(self, client_with_completed_tasks):
        response = client_with_completed_tasks.get(TASKS_ENDPOINT, params={'status': 'completed', 'start_date': '2000-01-01', 'limit': 1})
        assert len(response.json()) == 1, 'limit still caps a bounded read'

    def test_an_unparsable_bound_is_a_422(self, client_with_completed_tasks):
        response = client_with_completed_tasks.get(TASKS_ENDPOINT, params={'start_date': 'yesterday-ish'})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)


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
