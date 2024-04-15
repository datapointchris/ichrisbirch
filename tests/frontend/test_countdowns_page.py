import pytest
from playwright.sync_api import Page, expect

from ichrisbirch.config import get_settings

settings = get_settings()


@pytest.fixture
def homepage(page: Page):
    page.set_default_navigation_timeout(settings.playwright.timeout)
    page.set_default_timeout(settings.playwright.timeout)
    page.goto(f'{settings.flask.host}:{settings.flask.port}/countdowns/')
    yield


fake = {'name': 'Test Countdown', 'due date': '2050-01-01', 'notes': 'Test Notes'}


def test_countdowns_index(homepage, page: Page):
    expect(page).to_have_title('Countdowns')


def test_create_countdown(homepage, page: Page):
    page.get_by_label('name').fill(fake['name'])
    page.get_by_label('due date').fill(fake['due date'])
    page.get_by_label('notes').fill(fake['notes'])
    page.click('css=button[value="add"]')


def test_delete_countdown(homepage, page: Page):
    page.click('css=button[value="delete"]')
