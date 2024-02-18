import pytest
from playwright.sync_api import Page, expect

from ichrisbirch.config import get_settings
from tests.testing_data.tasks import BASE_DATA

settings = get_settings()


@pytest.fixture
def homepage(page: Page):
    page.set_default_navigation_timeout(settings.playwright.timeout)
    page.set_default_timeout(settings.playwright.timeout)
    page.goto(f'{settings.flask.host}:{settings.flask.port}/tasks/')
    yield


fake = {
    'name': 'Test Task',
    'category': 'Home',
    'priority': '50',
    'notes': 'Test Notes',
}


def test_tasks_index(homepage, page: Page):
    expect(page).to_have_title('Priority Tasks')


def test_create_task(homepage, page: Page):
    page.get_by_label('name').fill(fake['name'])
    page.get_by_label('category').select_option(fake['category'])
    page.get_by_label('priority').fill(fake['priority'])
    page.get_by_label('notes').fill(fake['notes'])
    page.query_selector('css=button[value="Add New Task"]').click()


def test_complete_task(homepage, page: Page):
    page.query_selector(f'css=button[value="{BASE_DATA[0].name} complete"]').click()
