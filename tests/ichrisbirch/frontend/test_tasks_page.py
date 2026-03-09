import pytest
from playwright.sync_api import Page
from playwright.sync_api import expect
from sqlalchemy import delete
from sqlalchemy import select

from ichrisbirch import models
from ichrisbirch.models.task import TaskCategory
from tests.factories import TaskFactory
from tests.factories import clear_factory_session
from tests.factories import set_factory_session
from tests.ichrisbirch.frontend.fixtures import FRONTEND_BASE_URL
from tests.ichrisbirch.frontend.fixtures import login_regular_user
from tests.utils.database import create_session
from tests.utils.database import test_settings


@pytest.fixture(autouse=True)
def setup_test_tasks(insert_users_for_login):
    """Create test tasks using factories for this test module."""
    with create_session(test_settings) as session:
        set_factory_session(session)
        TaskFactory(name='Fix the sink', category=TaskCategory.Home, priority=10, notes='Kitchen sink leaking')
        TaskFactory(name='Write tests', category=TaskCategory.Computer, priority=5, notes='Playwright tests')
        TaskFactory(name='Buy groceries', category=TaskCategory.Purchase, priority=15)
        session.commit()
        clear_factory_session()

    yield

    with create_session(test_settings) as session:
        session.execute(delete(models.Task))
        session.commit()


@pytest.fixture(autouse=True)
def login_homepage(setup_test_tasks, page: Page):
    login_regular_user(page)
    page.goto(f'{FRONTEND_BASE_URL}/tasks/')


def _get_task_from_db(name: str) -> models.Task:
    """Find a task by name via direct DB query."""
    with create_session(test_settings) as session:
        return session.execute(select(models.Task).where(models.Task.name == name)).scalar_one()


def _get_task_by_id_from_db(task_id: int) -> models.Task:
    """Get a task by ID via direct DB query."""
    with create_session(test_settings) as session:
        return session.execute(select(models.Task).where(models.Task.id == task_id)).scalar_one()


def _task_exists_in_db(task_id: int) -> bool:
    """Check if a task exists in DB."""
    with create_session(test_settings) as session:
        result = session.execute(select(models.Task).where(models.Task.id == task_id)).scalar_one_or_none()
        return result is not None


def test_tasks_index(page: Page):
    expect(page).to_have_title('Priority Tasks')


def test_create_task(page: Page):
    """Fill the add form on the dedicated add page, submit, verify in DB."""
    page.goto(f'{FRONTEND_BASE_URL}/tasks/add/')
    expect(page).to_have_title('Add New Task')

    form = page.locator('form.add-item-form')
    form.locator('#name').fill('Playwright Task')
    form.locator('#category').select_option('Computer')
    form.locator('#priority').fill('25')
    form.locator('#notes').fill('Created by Playwright')
    form.locator('button[value="add"]').click()

    task = _get_task_from_db('Playwright Task')
    assert task.category == TaskCategory.Computer
    assert task.priority == 25
    assert task.notes == 'Created by Playwright'
    assert task.complete_date is None


def test_create_task_via_footer(page: Page):
    """Create a task using the sticky footer form present on every task page."""
    page.goto(f'{FRONTEND_BASE_URL}/tasks/todo/')

    footer = page.locator('form.task-footer')
    footer.locator('#name').fill('Footer Task')
    footer.locator('#category').select_option('Chore')
    footer.locator('#priority').fill('20')
    footer.locator('#notes').fill('Created via footer')
    footer.locator('button[value="add"]').click()

    task = _get_task_from_db('Footer Task')
    assert task.category == TaskCategory.Chore
    assert task.priority == 20
    assert task.notes == 'Created via footer'


def test_complete_task(page: Page):
    """Complete a task via button click on the index page, verify in DB."""
    task = _get_task_from_db('Write tests')
    task_id = task.id
    assert task.complete_date is None

    task_form = page.locator(f'form:has(input[name="id"][value="{task_id}"])')
    task_form.locator('button[value="complete"]').click()

    result = _get_task_by_id_from_db(task_id)
    assert result.complete_date is not None, 'Task should have a complete_date'
    assert result.name == 'Write tests', 'Name should survive completion'


def test_extend_task_7_days(page: Page):
    """Extend a task by 7 days via the todo page, verify priority increases."""
    task = _get_task_from_db('Fix the sink')
    task_id = task.id
    original_priority = task.priority

    page.goto(f'{FRONTEND_BASE_URL}/tasks/todo/')
    task_form = page.locator(f'form:has(input[name="id"][value="{task_id}"])')
    task_form.locator('button[value="extend"]', has_text='7').click()

    result = _get_task_by_id_from_db(task_id)
    assert result.priority == original_priority + 7, 'Priority should increase by 7'
    assert result.notes == 'Kitchen sink leaking', 'Notes should survive extend'


def test_delete_task(page: Page):
    """Delete a task via button on the todo page, verify gone from DB."""
    task = _get_task_from_db('Buy groceries')
    task_id = task.id

    page.goto(f'{FRONTEND_BASE_URL}/tasks/todo/')
    task_form = page.locator(f'form:has(input[name="id"][value="{task_id}"])')
    task_form.locator('button[value="delete"]').click()

    assert not _task_exists_in_db(task_id), 'Task should be deleted'


def test_task_create_extend_complete_lifecycle(page: Page):
    """Create a task, extend it twice, then complete it.

    Tests state accumulation across the full task lifecycle — priority should
    accumulate extends, and all fields should survive each action.
    """
    # Create via the add page
    page.goto(f'{FRONTEND_BASE_URL}/tasks/add/')
    form = page.locator('form.add-item-form')
    form.locator('#name').fill('Lifecycle Task')
    form.locator('#category').select_option('Home')
    form.locator('#priority').fill('10')
    form.locator('#notes').fill('Full lifecycle test')
    form.locator('button[value="add"]').click()

    task = _get_task_from_db('Lifecycle Task')
    task_id = task.id
    assert task.priority == 10
    assert task.category == TaskCategory.Home

    # Extend by 7 days on the todo page
    page.goto(f'{FRONTEND_BASE_URL}/tasks/todo/')
    task_form = page.locator(f'form:has(input[name="id"][value="{task_id}"])')
    task_form.locator('button[value="extend"]', has_text='7').click()

    result = _get_task_by_id_from_db(task_id)
    assert result.priority == 17, 'Priority should be 10 + 7'
    assert result.notes == 'Full lifecycle test', 'Notes should survive extend'

    # Extend by 30 days
    task_form = page.locator(f'form:has(input[name="id"][value="{task_id}"])')
    task_form.locator('button[value="extend"]', has_text='30').click()

    result = _get_task_by_id_from_db(task_id)
    assert result.priority == 47, 'Priority should be 10 + 7 + 30'

    # Complete the task
    task_form = page.locator(f'form:has(input[name="id"][value="{task_id}"])')
    task_form.locator('button[value="complete"]').click()

    result = _get_task_by_id_from_db(task_id)
    assert result.complete_date is not None, 'Should be completed'
    assert result.name == 'Lifecycle Task', 'Name should survive completion'
    assert result.notes == 'Full lifecycle test', 'Notes should survive completion'
