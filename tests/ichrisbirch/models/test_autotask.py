from datetime import UTC
from datetime import date
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from ichrisbirch.models.autotask import AUTOTASK_FREQUENCIES
from ichrisbirch.models.autotask import AutoTask
from ichrisbirch.models.autotask import frequency_to_duration

NEW_YORK = ZoneInfo('America/New_York')


def last_ran(at: datetime, frequency: str = 'Daily') -> AutoTask:
    return AutoTask(name='Water plants', category='Chore', priority=1, frequency=frequency, last_run_date=at)


def test_every_frequency_has_a_duration():
    for frequency in AUTOTASK_FREQUENCIES:
        frequency_to_duration(frequency)


def test_an_unknown_frequency_is_refused():
    with pytest.raises(ValueError, match='Invalid frequency'):
        frequency_to_duration('Fortnightly')


@pytest.mark.parametrize(
    ('frequency', 'next_day'),
    [
        ('Daily', date(2026, 2, 1)),
        ('Weekly', date(2026, 2, 7)),
        ('Biweekly', date(2026, 2, 14)),
        ('Monthly', date(2026, 2, 28)),
        ('Quarterly', date(2026, 4, 30)),
        ('Semiannually', date(2026, 7, 31)),
        ('Yearly', date(2027, 1, 31)),
    ],
)
def test_the_next_run_is_counted_in_calendar_units(frequency, next_day):
    """A month is a calendar month, clamped to the shorter month's last day, not 30 days."""
    autotask = last_ran(datetime(2026, 1, 31, 12, tzinfo=UTC), frequency)

    assert autotask.next_run_day(ZoneInfo('UTC')) == next_day


def test_a_monthly_template_keeps_its_day_of_the_month():
    """Thirty days from January 15 is February 14, and the template would creep earlier every month."""
    autotask = last_ran(datetime(2026, 1, 15, 12, tzinfo=UTC), 'Monthly')

    assert autotask.next_run_day(ZoneInfo('UTC')) == date(2026, 2, 15)


def test_the_last_run_is_a_day_on_the_zones_calendar():
    """01:00 UTC on the 21st is 21:00 on the 20th in New York, so a daily template is next due on the 21st there."""
    autotask = last_ran(datetime(2026, 8, 21, 1, tzinfo=UTC))

    assert autotask.next_run_day(NEW_YORK) == date(2026, 8, 21)
    assert autotask.next_run_day(ZoneInfo('UTC')) == date(2026, 8, 22)


def test_a_template_is_due_on_its_next_run_day_and_after():
    autotask = last_ran(datetime(2026, 8, 20, 14, tzinfo=UTC), 'Weekly')

    assert not autotask.is_due_on(date(2026, 8, 26), NEW_YORK)
    assert autotask.is_due_on(date(2026, 8, 27), NEW_YORK)
    assert autotask.is_due_on(date(2026, 9, 3), NEW_YORK)


def test_a_template_that_ran_today_is_not_due_again_today():
    autotask = last_ran(datetime(2026, 8, 20, 14, tzinfo=UTC))

    assert not autotask.is_due_on(date(2026, 8, 20), NEW_YORK)
