from datetime import UTC
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from freezegun import freeze_time
from sqlalchemy import select

from ichrisbirch import models
from ichrisbirch.database.session import create_session
from ichrisbirch.scheduler import jobs
from tests.util import show_status_and_response
from tests.utils.database import delete_test_data
from tests.utils.database import insert_test_data
from tests.utils.database import test_settings


@pytest.fixture(autouse=True)
def insert_testing_data():
    insert_test_data('tasks')
    insert_test_data('autotasks')
    yield
    delete_test_data('tasks')
    delete_test_data('autotasks')


def _anchor_every_autotask(anchor: str) -> None:
    with create_session(test_settings) as session:
        for autotask in session.scalars(select(models.AutoTask)):
            autotask.anchor = anchor
        session.commit()


def _all_tasks(client) -> list[dict]:
    response = client.get('/tasks/', params={'status': 'all'})
    assert response.status_code == 200, show_status_and_response(response)
    return response.json()


def test_check_and_run_autotasks(test_api_logged_in):
    """Every base template last ran in 2020, so each adds one copy."""
    assert len(_all_tasks(test_api_logged_in)) == 3
    jobs.check_and_run_autotasks(test_settings)
    assert len(_all_tasks(test_api_logged_in)) == 6


def test_a_copy_records_its_template_and_window(test_api_logged_in):
    jobs.check_and_run_autotasks(test_settings)

    with create_session(test_settings) as session:
        templates = {a.id: a for a in session.scalars(select(models.AutoTask))}
    copies = [task for task in _all_tasks(test_api_logged_in) if task['autotask_id'] is not None]
    assert len(copies) == len(templates)
    for copy in copies:
        template = templates[copy['autotask_id']]
        assert copy['name'] == template.name
        assert copy['window_days'] == template.window_days


class TestCompletionAnchor:
    """A completion template has one open copy, and the next counts from when it closed."""

    WEEKLY = 'AutoTask 2 Home without notes window 10 not completed'

    def weekly_copies(self, client) -> list[dict]:
        return [task for task in _all_tasks(client) if task['name'] == self.WEEKLY]

    def test_an_open_copy_holds_the_next_one_back(self, test_api_logged_in):
        with freeze_time('2021-03-20'):
            jobs.check_and_run_autotasks(test_settings)
        with freeze_time('2022-03-20'):
            jobs.check_and_run_autotasks(test_settings)

        assert len(self.weekly_copies(test_api_logged_in)) == 1

    def test_the_next_copy_counts_from_the_completion(self, test_api_logged_in):
        with freeze_time('2021-03-20 12:00'):
            jobs.check_and_run_autotasks(test_settings)
        [copy] = self.weekly_copies(test_api_logged_in)
        with freeze_time('2021-04-10 12:00'):
            test_api_logged_in.patch(f'/tasks/{copy["id"]}/complete/')

        with freeze_time('2021-04-16 12:00'):
            jobs.check_and_run_autotasks(test_settings)
        assert len(self.weekly_copies(test_api_logged_in)) == 1, 'six days after completion is too soon'

        with freeze_time('2021-04-17 12:00'):
            jobs.check_and_run_autotasks(test_settings)
        assert len(self.weekly_copies(test_api_logged_in)) == 2, 'a week after completion is due'

    def test_a_dropped_copy_closes_it_like_a_completion(self, test_api_logged_in):
        with freeze_time('2021-03-20 12:00'):
            jobs.check_and_run_autotasks(test_settings)
        [copy] = self.weekly_copies(test_api_logged_in)
        with freeze_time('2021-04-10 12:00'):
            test_api_logged_in.patch(f'/tasks/{copy["id"]}/drop/')

        with freeze_time('2021-04-17 12:00'):
            jobs.check_and_run_autotasks(test_settings)
        assert len(self.weekly_copies(test_api_logged_in)) == 2


def test_check_and_run_autotasks_max_concurrent(test_api_logged_in):
    """A calendar template adds copies on schedule until max_concurrent are open."""
    _anchor_every_autotask('calendar')
    assert len(_all_tasks(test_api_logged_in)) == 3
    # base data has run dates of 2020
    with freeze_time('2021-03-20'):
        jobs.check_and_run_autotasks(test_settings)
        add_tasks = test_api_logged_in.get('/tasks/', params={'status': 'all'})
        assert add_tasks.status_code == 200, show_status_and_response(add_tasks)
        assert len(add_tasks.json()) == 6, add_tasks.json()
    # run autotask check again, giving all conccurent of 2
    with freeze_time('2022-03-20'):
        jobs.check_and_run_autotasks(test_settings)
        add_tasks_again = test_api_logged_in.get('/tasks/', params={'status': 'all'})
        assert add_tasks_again.status_code == 200, show_status_and_response(add_tasks_again)
        assert len(add_tasks_again.json()) == 9, add_tasks_again.json()
    # run autotask check, no new tasks should be added as all are at max_concurrent
    with freeze_time('2023-03-20'):
        jobs.check_and_run_autotasks(test_settings)
        no_add_tasks = test_api_logged_in.get('/tasks/', params={'status': 'all'})
        assert no_add_tasks.status_code == 200, show_status_and_response(no_add_tasks)
        assert len(no_add_tasks.json()) == 9, no_add_tasks.json()


def test_check_and_run_autotasks_completing_frees_a_slot(test_api_logged_in):
    """max_concurrent counts open tasks, not lifetime runs.

    Counting completed rows too turned it into a cap on how many times a template
    could ever fire, and every autotask stalled once its history reached the cap.
    """
    _anchor_every_autotask('calendar')
    baseline_ids = {task['id'] for task in test_api_logged_in.get('/tasks/', params={'status': 'all'}).json()}
    with freeze_time('2021-03-20'):
        jobs.check_and_run_autotasks(test_settings)
    with freeze_time('2022-03-20'):
        jobs.check_and_run_autotasks(test_settings)
    at_max = test_api_logged_in.get('/tasks/', params={'status': 'all'}).json()
    assert len(at_max) == 9, at_max

    spawned = [task for task in at_max if task['id'] not in baseline_ids]
    assert spawned, at_max
    for task in spawned:
        completed = test_api_logged_in.patch(f'/tasks/{task["id"]}/complete/')
        assert completed.status_code == 200, show_status_and_response(completed)

    with freeze_time('2023-03-20'):
        jobs.check_and_run_autotasks(test_settings)
    after = test_api_logged_in.get('/tasks/', params={'status': 'all'}).json()
    assert len(after) == 12, after


def _set_admin_zone(zone: str | None) -> None:
    with create_session(test_settings) as session:
        for admin in session.scalars(select(models.User).where(models.User.is_admin.is_(True))):
            admin.preferences = {**(admin.preferences or {}), 'timezone': zone}
        session.commit()


@pytest.fixture
def admin_in_new_york():
    _set_admin_zone('America/New_York')
    yield
    _set_admin_zone(None)


def test_the_scheduler_calendar_is_the_admins_zone(admin_in_new_york):
    with create_session(test_settings) as session:
        assert jobs.admin_calendar_zone(session) == ZoneInfo('America/New_York')


def test_the_scheduler_calendar_is_utc_before_the_admin_has_a_zone():
    with create_session(test_settings) as session:
        assert jobs.admin_calendar_zone(session) == ZoneInfo('UTC')


DAILY_NAME = 'Daily template last run at 10:00 in New York'


def _insert_daily_template_run_on_the_20th() -> None:
    with create_session(test_settings) as session:
        session.add(
            models.AutoTask(
                name=DAILY_NAME,
                category='Chore',
                frequency='Daily',
                first_run_date=datetime(2026, 8, 20, 14, tzinfo=UTC),
                last_run_date=datetime(2026, 8, 20, 14, tzinfo=UTC),
            )
        )
        session.commit()


def _spawned_from_daily_template(client) -> list[dict]:
    return [task for task in client.get('/tasks/', params={'status': 'all'}).json() if task['name'] == DAILY_NAME]


def test_an_autotask_is_due_by_the_admins_calendar(test_api_logged_in, admin_in_new_york):
    """02:00 UTC on the 21st is 22:00 on the 20th in New York, the day the template last ran."""
    _insert_daily_template_run_on_the_20th()

    with freeze_time(datetime(2026, 8, 21, 2, tzinfo=UTC)):
        jobs.check_and_run_autotasks(test_settings)

    assert _spawned_from_daily_template(test_api_logged_in) == []


def test_an_autotask_is_due_by_utc_before_the_admin_has_a_zone(test_api_logged_in):
    _insert_daily_template_run_on_the_20th()

    with freeze_time(datetime(2026, 8, 21, 2, tzinfo=UTC)):
        jobs.check_and_run_autotasks(test_settings)

    assert len(_spawned_from_daily_template(test_api_logged_in)) == 1


def test_the_overnight_jobs_fire_in_the_zone_they_are_given():
    zone = ZoneInfo('America/New_York')

    for job in jobs.get_jobs_to_add(test_settings, zone):
        assert job.trigger.timezone == zone, job.id
