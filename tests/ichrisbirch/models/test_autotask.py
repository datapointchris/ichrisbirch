from copy import deepcopy
from datetime import datetime
from datetime import timedelta

from ichrisbirch.models.autotask import AutoTaskFrequency
from ichrisbirch.models.autotask import frequency_to_duration
from tests.testing_data.autotasks import BASE_DATA

# TODO: [2023/06/14] - This is a hack for the sqlalchemy model that for some reason is
# returning a string for the date that needs to be parsed for the properties to work.
isoformat = '%Y-%m-%dT%H:%M:%S.%f'
autotasks_with_ids = []
for i, record in enumerate(deepcopy(BASE_DATA), start=1):
    record.id = i
    record.first_run_date = datetime.strptime(str(record.first_run_date), isoformat)
    record.last_run_date = datetime.strptime(str(record.last_run_date), isoformat)
    autotasks_with_ids.append(record)
    print(record)


def test_frequency_to_duration_enums():
    assert frequency_to_duration(AutoTaskFrequency.Daily.value).days == 1
    assert frequency_to_duration(AutoTaskFrequency.Weekly.value).days == 7
    assert frequency_to_duration(AutoTaskFrequency.Biweekly.value).days == 14
    assert frequency_to_duration(AutoTaskFrequency.Monthly.value).days == 30
    assert frequency_to_duration(AutoTaskFrequency.Quarterly.value).days == 90
    assert frequency_to_duration(AutoTaskFrequency.Semiannually.value).days == 180
    assert frequency_to_duration(AutoTaskFrequency.Yearly.value).days == 365


def test_frequency_to_duration_values():
    assert frequency_to_duration(AutoTaskFrequency.Daily.value).days == 1
    assert frequency_to_duration(AutoTaskFrequency.Weekly.value).days == 7
    assert frequency_to_duration(AutoTaskFrequency.Biweekly.value).days == 14
    assert frequency_to_duration(AutoTaskFrequency.Monthly.value).days == 30
    assert frequency_to_duration(AutoTaskFrequency.Quarterly.value).days == 90
    assert frequency_to_duration(AutoTaskFrequency.Semiannually.value).days == 180
    assert frequency_to_duration(AutoTaskFrequency.Yearly.value).days == 365


def test_frequency_to_duration_strings():
    assert frequency_to_duration('Daily').days == 1
    assert frequency_to_duration('Weekly').days == 7
    assert frequency_to_duration('Biweekly').days == 14
    assert frequency_to_duration('Monthly').days == 30
    assert frequency_to_duration('Quarterly').days == 90
    assert frequency_to_duration('Semiannually').days == 180
    assert frequency_to_duration('Yearly').days == 365


def test_autotask_frequency_is_correct():
    autotask = autotasks_with_ids[0]
    assert autotask.frequency == AutoTaskFrequency.Daily.value
    autotask = autotasks_with_ids[1]
    assert autotask.frequency == AutoTaskFrequency.Weekly.value
    autotask = autotasks_with_ids[2]
    assert autotask.frequency == AutoTaskFrequency.Quarterly.value


def test_autotask_frequency_is_correct_timedelta():
    autotask = autotasks_with_ids[0]
    assert frequency_to_duration(autotask.frequency).days == 1
    autotask = autotasks_with_ids[1]
    assert frequency_to_duration(autotask.frequency).days == 7
    autotask = autotasks_with_ids[2]
    assert frequency_to_duration(autotask.frequency).days == 90


def test_next_run_date_property():
    autotask = autotasks_with_ids[0]
    assert autotask.next_run_date == autotask.last_run_date.date() + timedelta(days=1)
    autotask = autotasks_with_ids[1]
    assert autotask.next_run_date == autotask.last_run_date.date() + timedelta(weeks=1)
    autotask = autotasks_with_ids[2]
    assert autotask.next_run_date == autotask.last_run_date.date() + timedelta(days=90)


def test_should_run_today_property():
    autotask = autotasks_with_ids[0]
    assert autotask.should_run_today is True
    autotask = autotasks_with_ids[1]
    assert autotask.should_run_today is True
    autotask = autotasks_with_ids[2]
    autotask.last_run_date = datetime.now()
    assert autotask.should_run_today is False
