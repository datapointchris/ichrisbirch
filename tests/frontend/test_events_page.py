import pytest
from playwright.sync_api import Page, expect


@pytest.fixture
def homepage(page: Page):
    timeout = 2_000
    page.set_default_navigation_timeout(timeout)
    page.set_default_timeout(timeout)
    page.goto('http://localhost:6200/events/')
    yield


def test_events_index(homepage, page: Page):
    expect(page).to_have_title('Events')


def test_create_event(homepage, page: Page):
    page.get_by_label('name').fill('Test Event')
    page.get_by_label('date').fill('2050-01-01')
    page.get_by_label('url').fill('https://example.com')
    page.get_by_label('venue').fill('Test Venue')
    page.get_by_label('cost').fill('20')
    page.get_by_label('attending').check()
    page.get_by_label('notes').fill('Test Notes')
    # page.get_by_label('method').fill('add')
    # page.get_by_role('submit', name='Add New Event').click()
