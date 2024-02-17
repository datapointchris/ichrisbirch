import pytest
from playwright.sync_api import Page, expect

from ichrisbirch.config import get_settings

settings = get_settings()


@pytest.fixture
def homepage(page: Page):
    timeout = 2_000
    page.set_default_navigation_timeout(timeout)
    page.set_default_timeout(timeout)
    page.goto(f'{settings.flask.host}:{settings.flask.port}/countdowns/')
    yield


def test_countdowns_index(homepage, page: Page):
    expect(page).to_have_title('Countdowns')


def test_create_countdown(homepage, page: Page):
    page.get_by_label('name').fill('Test Countdown')
    page.get_by_label('due date').fill('2050-01-01')
    page.get_by_label('notes').fill('Test Notes')
    page.get_by_role('button', name='add').click()


def test_delete_countdown(homepage, page: Page):
    page.get_by_text('Countdown 1 delete').click()
