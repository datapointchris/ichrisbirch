import pytest
from playwright.sync_api import Page
from playwright.sync_api import expect
from sqlalchemy import delete

from ichrisbirch import models
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
        AutoTaskFactory.create_batch(3)
        session.commit()
        clear_factory_session()

    yield

    # Cleanup: delete all autotasks
    with create_session(test_settings) as session:
        session.execute(delete(models.AutoTask))
        session.commit()


@pytest.fixture(autouse=True)
def login_homepage(setup_test_autotasks, page: Page):
    login_regular_user(page)
    page.goto(f'{FRONTEND_BASE_URL}/autotasks/')


fake = {
    'name': 'Test Autotask',
    'category': 'Home',
    'priority': '50',
    'notes': 'Test Notes',
    'frequency': 'Weekly',
}


def test_autotasks_index(page: Page):
    expect(page).to_have_title('AutoTasks')


def test_create_autotask(page: Page):
    page.get_by_label('name').fill(fake['name'])
    page.get_by_label('category').select_option(fake['category'])
    page.get_by_label('priority').fill(fake['priority'])
    page.get_by_label('notes').fill(fake['notes'])
    page.get_by_label('frequency').select_option(fake['frequency'])
    page.click('css=button[value="add"]')


def test_delete_autotask(page: Page):
    page.click('css=button[value="delete"]')
