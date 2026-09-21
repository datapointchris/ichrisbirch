"""Two releases write habit completions while a deploy switches colors.

The previous release writes `complete_date`, a moment, and reads it back through
a window of instants. This release writes `completion_date`, a day. A trigger
fills whichever of the two a row arrives without, so each release reads every
row the other wrote on the right day.
"""

import datetime as dt
from zoneinfo import ZoneInfo

import sqlalchemy as sa

from ichrisbirch import models
from tests.factories import HabitCategoryFactory

NEW_YORK = ZoneInfo('America/New_York')


def stored(session, completion_id: int) -> tuple[dt.datetime, dt.date]:
    row = session.execute(
        sa.text('SELECT complete_date, completion_date FROM habits.completed WHERE id = :id'),
        {'id': completion_id},
    ).one()
    return row.complete_date, row.completion_date


def insert_as_the_previous_release(session, category_id: int, moment: dt.datetime) -> int:
    return session.execute(
        sa.text("INSERT INTO habits.completed (name, category_id, complete_date) VALUES ('Floss', :category, :moment) RETURNING id"),
        {'category': category_id, 'moment': moment},
    ).scalar_one()


def test_a_moment_the_previous_release_writes_gets_its_new_york_day(factory_session):
    """01:30 UTC on the 21st is 21:30 on the 20th in New York."""
    moment = dt.datetime(2026, 9, 21, 1, 30, tzinfo=dt.UTC)
    completion_id = insert_as_the_previous_release(factory_session, HabitCategoryFactory().id, moment)

    _, day = stored(factory_session, completion_id)

    assert day == dt.date(2026, 9, 20)


def test_a_day_this_release_writes_is_noon_there_for_the_previous_one(factory_session):
    completion = models.HabitCompleted(name='Floss', category_id=HabitCategoryFactory().id, complete_date=dt.date(2026, 9, 20))
    factory_session.add(completion)
    factory_session.flush()

    moment, _ = stored(factory_session, completion.id)

    assert moment == dt.datetime(2026, 9, 20, 12, tzinfo=NEW_YORK)


def test_moving_the_day_moves_the_moment_with_it(factory_session):
    completion = models.HabitCompleted(name='Floss', category_id=HabitCategoryFactory().id, complete_date=dt.date(2026, 9, 20))
    factory_session.add(completion)
    factory_session.flush()

    completion.complete_date = dt.date(2026, 9, 18)
    factory_session.flush()

    moment, day = stored(factory_session, completion.id)
    assert (moment, day) == (dt.datetime(2026, 9, 18, 12, tzinfo=NEW_YORK), dt.date(2026, 9, 18))
