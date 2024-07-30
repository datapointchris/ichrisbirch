import pytest
from playwright.sync_api import Page
from playwright.sync_api import expect

import tests.util
from tests.ichrisbirch.frontend.fixtures import FRONTEND_BASE_URL
from tests.ichrisbirch.frontend.fixtures import login


@pytest.fixture(autouse=True)
def insert_testing_data():
    tests.util.insert_test_data('countdowns')
    yield
    tests.util.delete_test_data('countdowns')


@pytest.fixture(autouse=True)
def login_homepage(page: Page):
    """Automatically login with regular user Set the page to the base URL + endpoint.

    autouse=True means it does not need to be called in the test function
    """
    login(page)
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
