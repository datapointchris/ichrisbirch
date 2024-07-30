import pytest
from playwright.sync_api import Page
from playwright.sync_api import expect

import tests.util
from tests.ichrisbirch.frontend.fixtures import FRONTEND_BASE_URL
from tests.ichrisbirch.frontend.fixtures import login


@pytest.fixture(autouse=True)
def insert_testing_data():
    tests.util.insert_test_data('events')
    yield
    tests.util.delete_test_data('events')


@pytest.fixture(autouse=True)
def login_homepage(page: Page):
    """Automatically login with regular user Set the page to the base URL + endpoint.

    autouse=True means it does not need to be called in the test function
    """
    login(page)
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
