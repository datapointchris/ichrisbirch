from ichrisbirch.scheduler.jobs import JobToAdd
from ichrisbirch.scheduler.jobs import daily_3pm_trigger


def test_job_function_1():
    return 'Test Job Function 1'


def test_job_function_2():
    return 'Test Job Function 2'


def test_job_function_3():
    return 'Test Job Function 3'


BASE_DATA: list[JobToAdd] = [
    JobToAdd(func=test_job_function_1, trigger=daily_3pm_trigger, id='test_job_function_1'),
    JobToAdd(func=test_job_function_2, trigger=daily_3pm_trigger, id='test_job_function_2'),
    JobToAdd(func=test_job_function_3, trigger=daily_3pm_trigger, id='test_job_function_3'),
]
