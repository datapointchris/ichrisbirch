import pytest
from playwright.sync_api import Page, expect

from ichrisbirch.config import get_settings
from tests.testing_data.countdowns import BASE_DATA

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
    page.query_selector('css=button[value="Add Countdown"]').click()


def test_delete_countdown(homepage, page: Page):
    page.query_selector(f'css=button[value="{BASE_DATA[0].name} delete"]').click()
