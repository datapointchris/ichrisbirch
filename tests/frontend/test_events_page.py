import pytest
from playwright.sync_api import Page, expect

from ichrisbirch.config import get_settings
from tests.testing_data.events import BASE_DATA

settings = get_settings()


@pytest.fixture
def homepage(page: Page):
    page.set_default_navigation_timeout(settings.playwright.timeout)
    page.set_default_timeout(settings.playwright.timeout)
    page.goto(f'{settings.flask.host}:{settings.flask.port}/events/')
    yield


fake = {
    'name': 'Test Event',
    'date': '2050-01-01T00:00:00.123',
    'url': 'https://example.com',
    'venue': 'Test Venue',
    'cost': '20',
    'attending': 'on',
    'notes': 'Test Notes',
}


def test_events_index(homepage, page: Page):
    expect(page).to_have_title('Events')


def test_create_event(homepage, page: Page):
    page.get_by_label('name').fill(fake['name'])
    page.get_by_label('date').fill(fake['date'])
    page.get_by_label('url').fill(fake['url'])
    page.get_by_label('venue').fill(fake['venue'])
    page.get_by_label('cost').fill(fake['cost'])
    page.get_by_label('attending').check()
    page.get_by_label('notes').fill(fake['notes'])
    page.query_selector('css=button[value="Add Event"]').click()


def test_delete_event(homepage, page: Page):
    page.query_selector(f'css=button[value="{BASE_DATA[0].name} delete"]').click()


def test_attend_event(homepage, page: Page):
    # Event 2, BASE_DATA[1], attending=False
    page.query_selector(f'css=button[value="{BASE_DATA[1].name} attend"]').click()
