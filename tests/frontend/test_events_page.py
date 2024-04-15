import pytest
from playwright.sync_api import Page, expect

from ichrisbirch.config import get_settings

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
    page.click('css=button[value="add"]')


def test_delete_event(homepage, page: Page):
    page.click('css=button[value="delete"]')


def test_attend_event(homepage, page: Page):
    # Event 2, BASE_DATA[1], attending=False
    page.click('css=button[value="attend"]')
