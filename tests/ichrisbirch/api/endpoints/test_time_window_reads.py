"""`since` and `until` on the reads bounded by time.

Every such read takes its window through one dependency and one helper, so the
two column kinds are pinned once each: a timestamp column on `/articles` and a
calendar-day column on `/habits/completed`.
"""

import datetime as dt

import pytest
from fastapi import status

from ichrisbirch import models
from tests.util import show_status_and_response


def ok_rows(response) -> list[dict]:
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    return response.json()


@pytest.fixture
def client_with_read_dates(txn_api_logged_in):
    client, session = txn_api_logged_in
    session.add_all(
        [
            models.Article(
                title=title,
                url=f'http://example.com/{title}',
                tags=[],
                summary=f'{title} summary',
                save_date=dt.datetime(2026, 1, 1, tzinfo=dt.UTC),
                last_read_date=dt.datetime(2026, month, 15, 12, tzinfo=dt.UTC),
                read_count=1,
                is_favorite=False,
                is_current=False,
                is_archived=False,
            )
            for title, month in (('june', 6), ('july', 7), ('august', 8))
        ]
    )
    session.flush()
    return client


def article_titles(client, **window) -> set[str]:
    return {row['title'] for row in ok_rows(client.get('/articles', params=window))}


def test_since_is_inside_the_window_and_until_is_past_it(client_with_read_dates):
    """The rows are stamped at exactly the two edges, and either bound narrows alone."""
    july, august = '2026-07-15T12:00:00Z', '2026-08-15T08:00:00-04:00'

    assert article_titles(client_with_read_dates, since=july, until=august) == {'july'}
    assert article_titles(client_with_read_dates, since=july) == {'july', 'august'}
    assert article_titles(client_with_read_dates, until=july) == {'june'}


def test_a_calendar_day_column_is_read_in_the_request_zone(txn_api_logged_in):
    """A day is kept when its span in the zone overlaps the window.

    The UTC spelling of New York's midnight names the same instant, so it keeps
    the same days. A window ending at midnight stops before that day, and one
    ending later in the day reaches into it.
    """
    client, session = txn_api_logged_in
    category = models.HabitCategory(name='Windowed reads', is_current=True)
    session.add(category)
    session.flush()
    session.add_all(
        [models.HabitCompleted(name=f'day {day}', category_id=category.id, complete_date=dt.date(2026, 8, day)) for day in (14, 15, 16)]
    )
    session.flush()

    def days(since: str, until: str) -> list[str]:
        params = {'since': since, 'until': until, 'timezone': 'America/New_York'}
        return sorted(row['complete_date'] for row in ok_rows(client.get('/habits/completed', params=params)))

    assert days('2026-08-15T00:00:00-04:00', '2026-08-16T00:00:00-04:00') == ['2026-08-15']
    assert days('2026-08-15T04:00:00Z', '2026-08-16T04:00:00Z') == ['2026-08-15']
    assert days('2026-08-15T00:00:00-04:00', '2026-08-16T09:30:00-04:00') == ['2026-08-15', '2026-08-16']


@pytest.mark.parametrize(
    'window',
    [
        {'since': '2026-07-15'},
        {'until': '2026-07-15T12:00:00'},
        {'since': '7d'},
        {'since': '2026-08-01T00:00:00Z', 'until': '2026-07-01T00:00:00Z'},
    ],
    ids=['a bare day', 'no offset', 'a span', 'since after until'],
)
def test_a_bound_that_names_no_instant_or_runs_backward_is_a_422(client_with_read_dates, window):
    """The client resolves days and spans, so either reaching the API is a caller's mistake."""
    response = client_with_read_dates.get('/articles', params=window)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)
