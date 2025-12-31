"""End-to-end tests for the habits page functionality using Playwright.

Tests the habits index page, completed habits page, and habit management functionality.
"""

import pytest
from playwright.sync_api import Page
from playwright.sync_api import expect
from sqlalchemy import delete

from ichrisbirch import models
from tests.factories import HabitCategoryFactory
from tests.factories import HabitFactory
from tests.factories import clear_factory_session
from tests.factories import set_factory_session
from tests.ichrisbirch.frontend.fixtures import FRONTEND_BASE_URL
from tests.ichrisbirch.frontend.fixtures import login_regular_user
from tests.utils.database import create_session
from tests.utils.database import test_settings


@pytest.fixture(autouse=True)
def setup_test_habits(insert_users_for_login):
    """Create test habits using factories for this test module."""
    with create_session(test_settings) as session:
        set_factory_session(session)
        # Create categories with habits
        category1 = HabitCategoryFactory(name='Health')
        category2 = HabitCategoryFactory(name='Productivity')
        HabitFactory(name='Exercise', category=category1)
        HabitFactory(name='Meditate', category=category1)
        HabitFactory(name='Read', category=category2)
        session.commit()
        clear_factory_session()

    yield

    # Cleanup: delete in FK order (children first)
    with create_session(test_settings) as session:
        session.execute(delete(models.HabitCompleted))
        session.execute(delete(models.Habit))
        session.execute(delete(models.HabitCategory))
        session.commit()


@pytest.fixture(autouse=True)
def login_homepage(setup_test_habits, page: Page):
    login_regular_user(page)
    page.goto(f'{FRONTEND_BASE_URL}/habits/', timeout=10000)


FAKE_HABIT = {
    'name': 'Test Habit',
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

    # Select the first available category (ID is dynamic from factory)
    category_select = page.locator('select[name="category_id"]')
    if category_select.count() > 0:
        category_select.first.select_option(index=0)

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
