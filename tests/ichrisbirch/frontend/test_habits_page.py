"""End-to-end tests for the habits page functionality using Playwright.

Tests the habits index page, completed habits page, and habit management functionality.
"""

import pytest
from playwright.sync_api import Page
from playwright.sync_api import expect

from tests.ichrisbirch.frontend.fixtures import FRONTEND_BASE_URL
from tests.ichrisbirch.frontend.fixtures import login_regular_user
from tests.utils.database import delete_test_data
from tests.utils.database import insert_test_data


@pytest.fixture(autouse=True)
def insert_testing_data():
    """Insert test data before each test and clean up after."""
    insert_test_data('habitcategories', 'habits')
    yield
    delete_test_data('habitscompleted', 'habits', 'habitcategories')


@pytest.fixture(autouse=True)
def login_homepage(page: Page):
    login_regular_user(page)
    page.goto(f'{FRONTEND_BASE_URL}/habits/', timeout=10000)


FAKE_HABIT = {
    'name': 'Test Habit',
    'category_id': '1',
    'notes': 'Test habit notes',
}


def test_habits_index(page: Page):
    expect(page).to_have_title('Daily Habits')
    expect(page.locator('h1')).to_be_visible()
    expect(page.locator('body')).to_contain_text('Habits')
    assert 'habits' in page.url.lower(), f'Expected to be on habits page, but URL was {page.url}'


def test_complete_habit(page: Page):
    complete_buttons = page.locator('button[value="complete_habit"]')
    complete_buttons.first.click()
    expect(page).to_have_title('Daily Habits')
    expect(page).to_have_url(f'http://{FRONTEND_BASE_URL}/habits/')
    expect(page.locator('body')).to_contain_text('Habits')


def test_habits_completed_page(page: Page):
    page.goto(f'{FRONTEND_BASE_URL}/habits/completed/')
    expect(page).to_have_title('Completed Habits')
    expect(page.locator('body')).to_contain_text('Completed')
    assert 'habits/completed' in page.url.lower(), f'Expected to be on completed habits page, but URL was {page.url}'


def test_habits_manage_page(page: Page):
    page.goto(f'{FRONTEND_BASE_URL}/habits/manage/')
    expect(page).to_have_title('Manage Habits')
    expect(page.locator('body')).to_contain_text('Manage Habits')
    assert 'habits/manage' in page.url.lower(), f'Expected to be on habits manage page, but URL was {page.url}'


def test_add_new_habit(page: Page):
    page.goto(f'{FRONTEND_BASE_URL}/habits/manage/')
    page.locator('input[name="name"]').first.fill(FAKE_HABIT['name'])

    if page.locator('select[name="category_id"]').count() > 0:
        page.locator('select[name="category_id"]').first.select_option(FAKE_HABIT['category_id'])

    if page.locator('textarea[name="notes"]').count() > 0:
        page.locator('textarea[name="notes"]').first.fill(FAKE_HABIT['notes'])

    add_button = page.locator('button:has-text("Add New Habit")')
    add_button.click()
    page.wait_for_load_state('networkidle')
    expect(page.locator('body')).to_contain_text(FAKE_HABIT['name'])


def test_hibernate_and_revive_habit(page: Page):
    page.goto(f'{FRONTEND_BASE_URL}/habits/manage/')
    page.wait_for_load_state('networkidle')

    hibernate_button = page.locator('button[value="hibernate_habit"]').first
    expect(hibernate_button).to_be_visible()

    habit_container = hibernate_button.locator('xpath=./ancestor::*[position()=2]')
    habit_name = habit_container.text_content().strip().split('\n')[0].strip()

    hibernate_button.click()
    page.wait_for_load_state('networkidle')

    revive_button = page.locator('button[value="revive_habit"]').first
    expect(revive_button).to_be_visible()

    hibernated_container = revive_button.locator('xpath=./ancestor::*[position()=2]')
    expect(hibernated_container).to_contain_text(
        habit_name.split(' ')[0],
    )

    revive_button.click()
    page.wait_for_load_state('networkidle')

    revived_button = page.locator('button[value="hibernate_habit"]').first
    expect(revived_button).to_be_visible()


def test_add_new_category(page: Page):
    page.goto(f'{FRONTEND_BASE_URL}/habits/manage/')
    test_category_name = 'Test Category'

    # Look for the category name input by its ID
    category_input = page.locator('input#category_name')
    category_input.fill(test_category_name)

    # Click the add category button
    page.locator('button[value="add_category"]').click()

    # Wait for the page to reload after submission
    page.wait_for_load_state('networkidle')

    # Check if the category was added - using a more specific selector
    current_categories_section = page.locator('div.add-item-wrapper:has(h2:text("Current Categories"))')
    expect(current_categories_section).to_contain_text(test_category_name)
