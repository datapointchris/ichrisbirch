import pytest
from playwright.sync_api import Page
from playwright.sync_api import expect
from sqlalchemy import delete

from ichrisbirch import models
from tests.factories import CountdownFactory
from tests.factories import clear_factory_session
from tests.factories import set_factory_session
from tests.ichrisbirch.frontend.fixtures import FRONTEND_BASE_URL
from tests.ichrisbirch.frontend.fixtures import login_regular_user
from tests.utils.database import create_session
from tests.utils.database import test_settings


@pytest.fixture(autouse=True)
def setup_test_countdowns(insert_users_for_login):
    """Create test countdowns using factories for this test module."""
    with create_session(test_settings) as session:
        set_factory_session(session)
        CountdownFactory.create_batch(3)
        session.commit()
        clear_factory_session()

    yield

    # Cleanup: delete all countdowns
    with create_session(test_settings) as session:
        session.execute(delete(models.Countdown))
        session.commit()


@pytest.fixture(autouse=True)
def login_homepage(setup_test_countdowns, page: Page):
    """Automatically login with regular user Set the page to the base URL + endpoint.

    autouse=True means it does not need to be called in the test function
    """
    login_regular_user(page)
    page.goto(f'{FRONTEND_BASE_URL}/countdowns/')


fake = {'name': 'Test Countdown', 'due date': '2050-01-01', 'notes': 'Test Notes'}


def test_countdowns_index(page: Page):
    expect(page).to_have_title('Countdowns')


def test_create_countdown(page: Page):
    page.get_by_label('name').fill(fake['name'])
    page.get_by_label('due date').fill(fake['due date'])
    page.get_by_label('notes').fill(fake['notes'])
    page.click('css=button[value="add"]')


def test_delete_countdown(page: Page):
    page.click('css=button[value="delete"]')
