"""The day's habits board, tested without a database or an HTTP client.

The endpoint above this runs two queries and calls the functions in this module.
Every rule worth pinning — which zone's day, which completion matches which
habit, where an orphan sits — lives here, so a case costs a function call rather
than a container.
"""

import datetime as dt
from zoneinfo import ZoneInfo

from ichrisbirch import models
from ichrisbirch.services import habit_day

NEW_YORK = ZoneInfo('America/New_York')


def habit(id: int, name: str, category_id: int = 1) -> models.Habit:
    return models.Habit(id=id, name=name, category_id=category_id, is_current=True)


def completion(id: int, name: str, category_id: int = 1, habit_id: int | None = None) -> models.HabitCompleted:
    return models.HabitCompleted(
        id=id,
        habit_id=habit_id,
        name=name,
        category_id=category_id,
        complete_date=dt.datetime(2026, 9, 20, 12, 0, tzinfo=NEW_YORK),
    )


class TestDayBounds:
    def test_the_window_is_half_open(self):
        """A completion at the stroke of midnight belongs to the day it opens."""
        opens, closes = habit_day.day_bounds(dt.date(2026, 9, 20), NEW_YORK)

        assert opens == dt.datetime(2026, 9, 20, 0, 0, tzinfo=NEW_YORK)
        assert closes == dt.datetime(2026, 9, 21, 0, 0, tzinfo=NEW_YORK)

    def test_the_window_is_the_local_day_not_the_utc_one(self):
        """21:00 in New York is 01:00 tomorrow in UTC.

        A UTC window would report that completion against the wrong day and leave
        the habit reading as still due for the rest of the evening.
        """
        opens, closes = habit_day.day_bounds(dt.date(2026, 9, 20), NEW_YORK)

        evening = dt.datetime(2026, 9, 20, 21, 0, tzinfo=NEW_YORK)
        assert opens <= evening < closes
        assert evening.astimezone(dt.UTC).date() == dt.date(2026, 9, 21)

    def test_a_spring_forward_day_is_twenty_three_hours(self):
        """Built from the next calendar day, not by adding a fixed duration.

        Adding 24 hours to midnight lands at 01:00 on the day the offset moves,
        so an hour of the next day would be counted against this one.

        Measured in UTC. Subtracting two aware datetimes that share one tzinfo is
        computed as if both were naive, so `closes - opens` reads 24 hours here
        however far apart the two instants really are.
        """
        opens, closes = habit_day.day_bounds(dt.date(2026, 3, 8), NEW_YORK)

        assert closes.astimezone(dt.UTC) - opens.astimezone(dt.UTC) == dt.timedelta(hours=23)
        assert closes == dt.datetime(2026, 3, 9, 0, 0, tzinfo=NEW_YORK)

    def test_a_fall_back_day_is_twenty_five_hours(self):
        opens, closes = habit_day.day_bounds(dt.date(2026, 11, 1), NEW_YORK)

        assert closes.astimezone(dt.UTC) - opens.astimezone(dt.UTC) == dt.timedelta(hours=25)


class TestStillDue:
    def test_a_habit_with_no_completion_is_due(self):
        current = [habit(1, 'Floss'), habit(2, 'Yoga')]

        assert [h.id for h in habit_day.still_due(current, [])] == [1, 2]

    def test_a_completion_matches_its_habit_by_id(self):
        current = [habit(1, 'Floss'), habit(2, 'Yoga')]
        completed = [completion(10, 'Floss', habit_id=1)]

        assert [h.id for h in habit_day.still_due(current, completed)] == [2]

    def test_a_renamed_habit_is_still_matched_by_id(self):
        """The completion denormalized the old name, so only the id still matches."""
        current = [habit(1, 'Floss daily')]
        completed = [completion(10, 'Floss', habit_id=1)]

        assert habit_day.still_due(current, completed) == []

    def test_a_completion_with_no_id_falls_back_to_name_and_category(self):
        current = [habit(1, 'Floss')]
        completed = [completion(10, 'Floss', habit_id=None)]

        assert habit_day.still_due(current, completed) == []

    def test_the_fallback_does_not_reach_across_categories(self):
        """Two habits can share a name. Keyed on the name alone, one completion
        of `Read` under Health would also tick off `Read` under Mind."""
        current = [habit(1, 'Read', category_id=1), habit(2, 'Read', category_id=2)]
        completed = [completion(10, 'Read', category_id=1, habit_id=None)]

        assert [h.id for h in habit_day.still_due(current, completed)] == [2]

    def test_a_completion_whose_habit_is_gone_leaves_the_rest_due(self):
        current = [habit(1, 'Floss')]
        completed = [completion(10, 'Retired habit', habit_id=None)]

        assert [h.id for h in habit_day.still_due(current, completed)] == [1]


class TestPlacement:
    def test_rows_order_by_habit_id(self):
        assert sorted([8, 2, 5], key=habit_day.placement) == [2, 5, 8]

    def test_a_row_with_no_habit_id_sorts_last(self):
        """It has no habit to place it by, and going first would push every habit
        you still owe down a row."""
        assert sorted([None, 1], key=habit_day.placement) == [1, None]


class TestHabitKey:
    def test_the_separator_keeps_a_category_off_a_numeric_name(self):
        """`11` + `Read` and `1` + `1Read` are different habits, and a key that
        concatenated them would read as one."""
        assert habit_day.habit_key('Read', 11) != habit_day.habit_key('1Read', 1)
