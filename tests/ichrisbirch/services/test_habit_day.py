"""The day's habits board, tested without a database or an HTTP client.

The endpoint above this runs two queries and calls the functions in this module.
Every rule worth pinning — which completion matches which habit, where an orphan
sits — lives here, so a case costs a function call rather than a container.
"""

import datetime as dt

from ichrisbirch import models
from ichrisbirch.services import habit_day


def habit(id: int, name: str, category_id: int = 1) -> models.Habit:
    return models.Habit(id=id, name=name, category_id=category_id, is_current=True)


def completion(id: int, name: str, category_id: int = 1, habit_id: int | None = None) -> models.HabitCompleted:
    return models.HabitCompleted(
        id=id,
        habit_id=habit_id,
        name=name,
        category_id=category_id,
        complete_date=dt.date(2026, 9, 20),
    )


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
