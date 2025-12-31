from datetime import datetime

import pytest
from playwright.sync_api import Page
from playwright.sync_api import expect
from sqlalchemy import delete

from ichrisbirch import models
from tests.factories import EventFactory
from tests.factories import clear_factory_session
from tests.factories import set_factory_session
from tests.ichrisbirch.frontend.fixtures import FRONTEND_BASE_URL
from tests.ichrisbirch.frontend.fixtures import login_regular_user
from tests.utils.database import create_session
from tests.utils.database import test_settings


@pytest.fixture(autouse=True)
def setup_test_events(insert_users_for_login):
    """Create test events using factories for this test module."""
    with create_session(test_settings) as session:
        set_factory_session(session)
        # Create events with specific attending states for testing
        EventFactory(name='Event 1', attending=True, date=datetime(2022, 10, 1, 10).isoformat())
        EventFactory(name='Event 2', attending=False, date=datetime(2022, 10, 2, 14).isoformat())
        EventFactory(name='Event 3', attending=True, date=datetime(2022, 10, 3, 18).isoformat())
        session.commit()
        clear_factory_session()

    yield

    # Cleanup: delete all events
    with create_session(test_settings) as session:
        session.execute(delete(models.Event))
        session.commit()


@pytest.fixture(autouse=True)
def login_homepage(setup_test_events, page: Page):
    """Automatically login with regular user Set the page to the base URL + endpoint.

    autouse=True means it does not need to be called in the test function
    """
    login_regular_user(page)
    page.goto(f'{FRONTEND_BASE_URL}/events/')


fake = {
    'name': 'Test Event',
    'date': '2050-01-01T00:00:00.123',
    'url': 'https://example.com',
    'venue': 'Test Venue',
    'cost': '20',
    'attending': 'on',
    'notes': 'Test Notes',
}


def test_events_index(page: Page):
    expect(page).to_have_title('Events')


def test_create_event(page: Page):
    page.get_by_label('name').fill(fake['name'])
    page.get_by_label('date').fill(fake['date'])
    page.get_by_label('url').fill(fake['url'])
    page.get_by_label('venue').fill(fake['venue'])
    page.get_by_label('cost').fill(fake['cost'])
    page.get_by_label('attending').check()
    page.get_by_label('notes').fill(fake['notes'])
    page.click('css=button[value="add"]')


def test_delete_event(page: Page):
    page.click('css=button[value="delete"]')


def test_attend_event(page: Page):
    # Event 2, BASE_DATA[1], attending=False
    page.click('css=button[value="attend"]')
