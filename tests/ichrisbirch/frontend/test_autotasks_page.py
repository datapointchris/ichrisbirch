import pytest
from playwright.sync_api import Page
from playwright.sync_api import expect
from sqlalchemy import delete
from sqlalchemy import select

from ichrisbirch import models
from ichrisbirch.models.autotask import AutoTaskFrequency
from ichrisbirch.models.task import TaskCategory
from tests.factories import AutoTaskFactory
from tests.factories import clear_factory_session
from tests.factories import set_factory_session
from tests.ichrisbirch.frontend.fixtures import FRONTEND_BASE_URL
from tests.ichrisbirch.frontend.fixtures import login_regular_user
from tests.utils.database import create_session
from tests.utils.database import test_settings


@pytest.fixture(autouse=True)
def setup_test_autotasks(insert_users_for_login):
    """Create test autotasks using factories for this test module."""
    with create_session(test_settings) as session:
        set_factory_session(session)
        AutoTaskFactory(name='Daily Cleanup', category=TaskCategory.Chore, frequency=AutoTaskFrequency.Daily, priority=5)
        AutoTaskFactory(name='Weekly Review', category=TaskCategory.Computer, frequency=AutoTaskFrequency.Weekly, priority=10)
        AutoTaskFactory(name='Monthly Budget', category=TaskCategory.Financial, frequency=AutoTaskFrequency.Monthly, priority=15)
        session.commit()
        clear_factory_session()

    yield

    with create_session(test_settings) as session:
        session.execute(delete(models.AutoTask))
        session.execute(delete(models.Task))
        session.commit()


@pytest.fixture(autouse=True)
def login_homepage(setup_test_autotasks, page: Page):
    login_regular_user(page)
    page.goto(f'{FRONTEND_BASE_URL}/autotasks/')


def _get_autotask_from_db(name: str) -> models.AutoTask:
    """Find an autotask by name via direct DB query."""
    with create_session(test_settings) as session:
        return session.execute(select(models.AutoTask).where(models.AutoTask.name == name)).scalar_one()


def _autotask_exists_in_db(autotask_id: int) -> bool:
    """Check if an autotask exists in DB."""
    with create_session(test_settings) as session:
        result = session.execute(select(models.AutoTask).where(models.AutoTask.id == autotask_id)).scalar_one_or_none()
        return result is not None


def _get_task_from_db(name: str) -> models.Task | None:
    """Find a task by name via direct DB query."""
    with create_session(test_settings) as session:
        return session.execute(select(models.Task).where(models.Task.name == name)).scalar_one_or_none()


def test_autotasks_index(page: Page):
    expect(page).to_have_title('AutoTasks')
    # All 3 autotasks should be visible
    expect(page.locator('.grid__item h2')).to_have_count(3)


def test_create_autotask(page: Page):
    """Fill the add form, submit, verify autotask and its side-effect task in DB.

    Creating an autotask immediately runs it, which creates a Task.
    """
    form = page.locator('form.add-item-form')
    form.locator('#name').fill('Playwright AutoTask')
    form.locator('#priority').fill('25')
    form.locator('#category').select_option('Home')
    form.locator('#frequency').select_option('Biweekly')
    form.locator('#notes').fill('Created by Playwright')
    form.locator('button[value="add"]').click()

    autotask = _get_autotask_from_db('Playwright AutoTask')
    assert autotask.category == TaskCategory.Home
    assert autotask.priority == 25
    assert autotask.frequency == AutoTaskFrequency.Biweekly
    assert autotask.notes == 'Created by Playwright'
    assert autotask.run_count == 1, 'Add should immediately run the autotask'

    # Verify the side-effect: a Task should have been created
    task = _get_task_from_db('Playwright AutoTask')
    assert task is not None, 'Running an autotask should create a Task'
    assert task.category == TaskCategory.Home
    assert task.priority == 25


def test_run_autotask(page: Page):
    """Run an existing autotask, verify it creates a Task in DB."""
    autotask = _get_autotask_from_db('Weekly Review')
    autotask_id = autotask.id

    autotask_form = page.locator(f'form:has(input[name="id"][value="{autotask_id}"])')
    autotask_form.locator('button[value="run"]').click()

    # Verify the autotask's run_count incremented
    result = _get_autotask_from_db('Weekly Review')
    assert result.run_count == 1, 'Run count should increment'

    # Verify a Task was created
    task = _get_task_from_db('Weekly Review')
    assert task is not None, 'Running should create a Task'
    assert task.category == TaskCategory.Computer


def test_delete_autotask(page: Page):
    """Delete a specific autotask via button click, verify it's gone from DB."""
    autotask = _get_autotask_from_db('Monthly Budget')
    autotask_id = autotask.id

    autotask_form = page.locator(f'form:has(input[name="id"][value="{autotask_id}"])')
    autotask_form.locator('button[value="delete"]').click()

    assert not _autotask_exists_in_db(autotask_id), 'AutoTask should be deleted'


def test_autotask_create_run_delete_lifecycle(page: Page):
    """Create an autotask, run it again, then delete it.

    Tests state accumulation: create (runs once) -> run (runs again) -> delete.
    """
    # Create
    form = page.locator('form.add-item-form')
    form.locator('#name').fill('Lifecycle AutoTask')
    form.locator('#priority').fill('8')
    form.locator('#category').select_option('Personal')
    form.locator('#frequency').select_option('Weekly')
    form.locator('#notes').fill('Lifecycle test')
    form.locator('button[value="add"]').click()

    autotask = _get_autotask_from_db('Lifecycle AutoTask')
    autotask_id = autotask.id
    assert autotask.run_count == 1, 'Should have run once on create'

    # Run it again
    autotask_form = page.locator(f'form:has(input[name="id"][value="{autotask_id}"])')
    autotask_form.locator('button[value="run"]').click()

    result = _get_autotask_from_db('Lifecycle AutoTask')
    assert result.run_count == 2, 'Run count should be 2 after second run'
    assert result.notes == 'Lifecycle test', 'Notes should survive run'

    # Delete
    autotask_form = page.locator(f'form:has(input[name="id"][value="{autotask_id}"])')
    autotask_form.locator('button[value="delete"]').click()

    assert not _autotask_exists_in_db(autotask_id), 'AutoTask should be deleted'
