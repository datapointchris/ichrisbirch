import pytest
from playwright.sync_api import Page
from playwright.sync_api import expect

import tests.util
from tests.ichrisbirch.frontend.fixtures import FRONTEND_BASE_URL
from tests.ichrisbirch.frontend.fixtures import login


@pytest.fixture(autouse=True)
def insert_testing_data():
    tests.util.insert_test_data('tasks')
    yield
    tests.util.delete_test_data('tasks')


@pytest.fixture(autouse=True)
def login_homepage(page: Page):
    """Automatically login with regular user Set the page to the base URL + endpoint.

    autouse=True means it does not need to be called in the test function
    """
    login(page)
    page.goto(f'{FRONTEND_BASE_URL}/tasks/')


fake = {
    'name': 'Test Task',
    'category': 'Home',
    'priority': '50',
    'notes': 'Test Notes',
}


def test_tasks_index(page: Page):
    expect(page).to_have_title('Priority Tasks')


@pytest.mark.skip(reason='Playwright reports that the button is outside the viewport')
def test_create_task(page: Page):
    page.get_by_label('name').fill(fake['name'])
    page.get_by_label('category').select_option(fake['category'])
    page.get_by_label('priority').fill(fake['priority'])
    page.get_by_label('notes').fill(fake['notes'])
    # BUG: Playwright reports that the button is outside the viewport
    page.click('css=button[value="add"]')


def test_complete_task(page: Page):
    page.click('css=button[value="complete"]')
