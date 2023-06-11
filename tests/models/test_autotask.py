from copy import deepcopy
from datetime import datetime, timedelta

from ichrisbirch import models, schemas
from ichrisbirch.models.autotask import TaskFrequency, frequency_to_duration
from tests.testing_data.autotasks import AUTOTASK_TEST_DATA

autotasks_with_ids = []
for i, record in enumerate(deepcopy(AUTOTASK_TEST_DATA), start=1):
    record['id'] = i
    autotasks_with_ids.append(models.AutoTask(**(schemas.AutoTask(**record).dict())))


def test_frequency_to_duration_enums():
    assert frequency_to_duration(TaskFrequency.Daily.value).days == 1
    assert frequency_to_duration(TaskFrequency.Weekly.value).days == 7
    assert frequency_to_duration(TaskFrequency.Biweekly.value).days == 14
    assert frequency_to_duration(TaskFrequency.Monthly.value).days == 30
    assert frequency_to_duration(TaskFrequency.Quarterly.value).days == 90
    assert frequency_to_duration(TaskFrequency.Semiannual.value).days == 180
    assert frequency_to_duration(TaskFrequency.Yearly.value).days == 365


def test_frequency_to_duration_values():
    assert frequency_to_duration(TaskFrequency.Daily.value).days == 1
    assert frequency_to_duration(TaskFrequency.Weekly.value).days == 7
    assert frequency_to_duration(TaskFrequency.Biweekly.value).days == 14
    assert frequency_to_duration(TaskFrequency.Monthly.value).days == 30
    assert frequency_to_duration(TaskFrequency.Quarterly.value).days == 90
    assert frequency_to_duration(TaskFrequency.Semiannual.value).days == 180
    assert frequency_to_duration(TaskFrequency.Yearly.value).days == 365


def test_frequency_to_duration_strings():
    assert frequency_to_duration('Daily').days == 1
    assert frequency_to_duration('Weekly').days == 7
    assert frequency_to_duration('Biweekly').days == 14
    assert frequency_to_duration('Monthly').days == 30
    assert frequency_to_duration('Quarterly').days == 90
    assert frequency_to_duration('Semiannual').days == 180
    assert frequency_to_duration('Yearly').days == 365


def test_autotask_frequency_is_correct():
    autotask = autotasks_with_ids[0]
    assert autotask.frequency == TaskFrequency.Daily.value
    autotask = autotasks_with_ids[1]
    assert autotask.frequency == TaskFrequency.Weekly.value
    autotask = autotasks_with_ids[2]
    assert autotask.frequency == TaskFrequency.Quarterly.value


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
