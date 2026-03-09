import pytest
from playwright.sync_api import Page
from playwright.sync_api import expect
from sqlalchemy import delete
from sqlalchemy import select

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
        cat_health = HabitCategoryFactory(name='Health')
        cat_prod = HabitCategoryFactory(name='Productivity')
        HabitFactory(name='Exercise', category=cat_health)
        HabitFactory(name='Meditate', category=cat_health)
        HabitFactory(name='Read', category=cat_prod)
        session.commit()
        clear_factory_session()

    yield

    with create_session(test_settings) as session:
        session.execute(delete(models.HabitCompleted))
        session.execute(delete(models.Habit))
        session.execute(delete(models.HabitCategory))
        session.commit()


@pytest.fixture(autouse=True)
def login_homepage(setup_test_habits, page: Page):
    login_regular_user(page)
    page.goto(f'{FRONTEND_BASE_URL}/habits/')


def _get_habit_from_db(name: str) -> models.Habit:
    with create_session(test_settings) as session:
        return session.execute(select(models.Habit).where(models.Habit.name == name)).scalar_one()


def _get_habit_by_id_from_db(habit_id: int) -> models.Habit | None:
    with create_session(test_settings) as session:
        return session.execute(select(models.Habit).where(models.Habit.id == habit_id)).scalar_one_or_none()


def _get_category_from_db(name: str) -> models.HabitCategory:
    with create_session(test_settings) as session:
        return session.execute(select(models.HabitCategory).where(models.HabitCategory.name == name)).scalar_one()


def _get_category_by_id_from_db(cat_id: int) -> models.HabitCategory | None:
    with create_session(test_settings) as session:
        return session.execute(select(models.HabitCategory).where(models.HabitCategory.id == cat_id)).scalar_one_or_none()


def _count_completed_habits_in_db() -> int:
    with create_session(test_settings) as session:
        return session.execute(select(models.HabitCompleted)).scalars().all().__len__()


def test_habits_index(page: Page):
    expect(page).to_have_title('Daily Habits')
    # All 3 habits should appear in "To Do"
    expect(page.locator('button[value="complete_habit"]')).to_have_count(3)


def test_complete_habit(page: Page):
    """Complete a habit on the index page, verify HabitCompleted record in DB."""
    assert _count_completed_habits_in_db() == 0

    # Find the Exercise habit's form by its hidden name field
    habit_form = page.locator('form:has(input[name="name"][value="Exercise"])')
    habit_form.locator('button[value="complete_habit"]').click()

    assert _count_completed_habits_in_db() == 1

    # The completed habit should now appear in "Done" column, not "To Do"
    expect(page.locator('button[value="complete_habit"]')).to_have_count(2)


def test_completed_page(page: Page):
    page.goto(f'{FRONTEND_BASE_URL}/habits/completed/')
    expect(page).to_have_title('Completed Habits')


def test_manage_page(page: Page):
    page.goto(f'{FRONTEND_BASE_URL}/habits/manage/')
    expect(page).to_have_title('Manage Habits')


def test_add_habit(page: Page):
    """Add a new habit via the manage page, verify in DB."""
    page.goto(f'{FRONTEND_BASE_URL}/habits/manage/')

    page.locator('#habit_name').fill('New Habit')
    page.locator('#habit_category').select_option(label='Health')
    page.locator('button[value="add_habit"]').click()

    habit = _get_habit_from_db('New Habit')
    assert habit.is_current is True
    cat = _get_category_from_db('Health')
    assert habit.category_id == cat.id


def test_add_category(page: Page):
    """Add a new category via the manage page, verify in DB."""
    page.goto(f'{FRONTEND_BASE_URL}/habits/manage/')

    page.locator('#category_name').fill('Fitness')
    page.locator('button[value="add_category"]').click()

    category = _get_category_from_db('Fitness')
    assert category.is_current is True


def test_hibernate_and_revive_habit(page: Page):
    """Hibernate a habit, verify state, then revive it."""
    habit = _get_habit_from_db('Exercise')
    habit_id = habit.id
    assert habit.is_current is True

    page.goto(f'{FRONTEND_BASE_URL}/habits/manage/')

    # Hibernate
    habit_form = page.locator(f'form:has(input[name="id"][value="{habit_id}"])')
    habit_form.locator('button[value="hibernate_habit"]').click()

    result = _get_habit_by_id_from_db(habit_id)
    assert result.is_current is False, 'Habit should be hibernated'

    # Revive
    habit_form = page.locator(f'form:has(input[name="id"][value="{habit_id}"])')
    habit_form.locator('button[value="revive_habit"]').click()

    result = _get_habit_by_id_from_db(habit_id)
    assert result.is_current is True, 'Habit should be revived'


def test_hibernate_and_revive_category(page: Page):
    """Hibernate a category, verify state, then revive it."""
    category = _get_category_from_db('Productivity')
    cat_id = category.id

    page.goto(f'{FRONTEND_BASE_URL}/habits/manage/')

    # Hibernate
    cat_form = page.locator(f'form:has(input[name="id"][value="{cat_id}"]):has(button[value="hibernate_category"])')
    cat_form.locator('button[value="hibernate_category"]').click()

    result = _get_category_by_id_from_db(cat_id)
    assert result.is_current is False, 'Category should be hibernated'

    # Revive
    cat_form = page.locator(f'form:has(input[name="id"][value="{cat_id}"]):has(button[value="revive_category"])')
    cat_form.locator('button[value="revive_category"]').click()

    result = _get_category_by_id_from_db(cat_id)
    assert result.is_current is True, 'Category should be revived'


def test_habit_lifecycle(page: Page):
    """Add category, add habit, complete it, hibernate it, delete it.

    Tests the full lifecycle of a habit through multiple state transitions.
    """
    # Add a category
    page.goto(f'{FRONTEND_BASE_URL}/habits/manage/')
    page.locator('#category_name').fill('Lifecycle Category')
    page.locator('button[value="add_category"]').click()

    category = _get_category_from_db('Lifecycle Category')

    # Add a habit in that category
    page.locator('#habit_name').fill('Lifecycle Habit')
    page.locator('#habit_category').select_option(label='Lifecycle Category')
    page.locator('button[value="add_habit"]').click()

    habit = _get_habit_from_db('Lifecycle Habit')
    habit_id = habit.id
    assert habit.is_current is True
    assert habit.category_id == category.id

    # Complete the habit on the index page
    page.goto(f'{FRONTEND_BASE_URL}/habits/')
    habit_form = page.locator('form:has(input[name="name"][value="Lifecycle Habit"])')
    habit_form.locator('button[value="complete_habit"]').click()

    assert _count_completed_habits_in_db() == 1

    # Hibernate the habit
    page.goto(f'{FRONTEND_BASE_URL}/habits/manage/')
    habit_form = page.locator(f'form:has(input[name="id"][value="{habit_id}"])')
    habit_form.locator('button[value="hibernate_habit"]').click()

    result = _get_habit_by_id_from_db(habit_id)
    assert result.is_current is False

    # Delete the hibernated habit
    habit_form = page.locator(f'form:has(input[name="id"][value="{habit_id}"])')
    habit_form.locator('button[value="delete_habit"]').click()

    assert _get_habit_by_id_from_db(habit_id) is None, 'Habit should be deleted'
