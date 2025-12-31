import pytest
from playwright.sync_api import Page
from playwright.sync_api import expect
from sqlalchemy import delete

from ichrisbirch import models
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
        TaskFactory.create_batch(3)
        session.commit()
        clear_factory_session()

    yield

    # Cleanup: delete all tasks
    with create_session(test_settings) as session:
        session.execute(delete(models.Task))
        session.commit()


@pytest.fixture(autouse=True)
def login_homepage(setup_test_tasks, page: Page):
    """Automatically login with regular user Set the page to the base URL + endpoint.

    autouse=True means it does not need to be called in the test function
    """
    login_regular_user(page)
    page.goto(f'{FRONTEND_BASE_URL}/tasks/')


fake = {
    'name': 'Test Task',
    'category': 'Home',
    'priority': '50',
    'notes': 'Test Notes',
}


def test_tasks_index(page: Page):
    expect(page).to_have_title('Priority Tasks')


@pytest.mark.skip(reason='Playwright reports that the button is outside the viewport')
def test_create_task(page: Page):
    page.get_by_label('name').fill(fake['name'])
    page.get_by_label('category').select_option(fake['category'])
    page.get_by_label('priority').fill(fake['priority'])
    page.get_by_label('notes').fill(fake['notes'])
    # BUG: Playwright reports that the button is outside the viewport
    page.click('css=button[value="add"]')


def test_complete_task(page: Page):
    page.click('css=button[value="complete"]')
