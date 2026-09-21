from zoneinfo import ZoneInfo

from apscheduler.triggers.cron import CronTrigger

from ichrisbirch.scheduler.jobs import JobToAdd

daily_3pm_trigger = CronTrigger(hour=15, timezone=ZoneInfo('UTC'))


class DummySettings:
    CLASS_NAME = 'DummySettings'


dummy_settings = DummySettings()


def test_job_function_1(settings: DummySettings):
    return f'Test Job Function 1: settings class {settings.CLASS_NAME}'


def test_job_function_2(settings: DummySettings):
    return f'Test Job Function 2: settings class {settings.CLASS_NAME}'


def test_job_function_3(settings: DummySettings):
    return f'Test Job Function 3: settings class {settings.CLASS_NAME}'


BASE_DATA: list[JobToAdd] = [
    JobToAdd(func=test_job_function_1, args=(dummy_settings,), trigger=daily_3pm_trigger, id='test_job_function_1'),
    JobToAdd(func=test_job_function_2, args=(dummy_settings,), trigger=daily_3pm_trigger, id='test_job_function_2'),
    JobToAdd(func=test_job_function_3, args=(dummy_settings,), trigger=daily_3pm_trigger, id='test_job_function_3'),
]
