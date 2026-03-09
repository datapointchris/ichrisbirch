import pytest
from playwright.sync_api import Page
from playwright.sync_api import expect
from sqlalchemy import delete
from sqlalchemy import select

from ichrisbirch import models
from tests.factories import CountdownFactory
from tests.factories import clear_factory_session
from tests.factories import set_factory_session
from tests.ichrisbirch.frontend.fixtures import FRONTEND_BASE_URL
from tests.ichrisbirch.frontend.fixtures import login_regular_user
from tests.utils.database import create_session
from tests.utils.database import test_settings


@pytest.fixture(autouse=True)
def setup_test_countdowns(insert_users_for_login):
    """Create test countdowns using factories for this test module."""
    with create_session(test_settings) as session:
        set_factory_session(session)
        CountdownFactory(name='Holiday Countdown', notes='Time off', due_date='2050-12-25')
        CountdownFactory(name='Project Deadline', notes='Ship it', due_date='2050-06-01')
        CountdownFactory(name='Birthday Party', notes='Celebrate', due_date='2050-09-15')
        session.commit()
        clear_factory_session()

    yield

    with create_session(test_settings) as session:
        session.execute(delete(models.Countdown))
        session.commit()


@pytest.fixture(autouse=True)
def login_homepage(setup_test_countdowns, page: Page):
    login_regular_user(page)
    page.goto(f'{FRONTEND_BASE_URL}/countdowns/')


def _get_countdown_from_db(name: str) -> models.Countdown:
    """Find a countdown by name via direct DB query."""
    with create_session(test_settings) as session:
        return session.execute(select(models.Countdown).where(models.Countdown.name == name)).scalar_one()


def _countdown_exists_in_db(countdown_id: int) -> bool:
    """Check if a countdown exists in DB."""
    with create_session(test_settings) as session:
        result = session.execute(select(models.Countdown).where(models.Countdown.id == countdown_id)).scalar_one_or_none()
        return result is not None


def test_countdowns_index(page: Page):
    expect(page).to_have_title('Countdowns')
    # All 3 countdowns should be visible
    expect(page.locator('.grid__item h2').first).to_be_visible()


def test_create_countdown(page: Page):
    """Fill the add form in a real browser, submit, verify in DB."""
    form = page.locator('form.add-item-form')
    form.locator('#name').fill('Playwright Countdown')
    form.locator('#due_date').fill('2051-03-15')
    form.locator('#notes').fill('Created by Playwright')
    form.locator('button[value="add"]').click()

    countdown = _get_countdown_from_db('Playwright Countdown')
    assert countdown.notes == 'Created by Playwright'
    assert str(countdown.due_date) == '2051-03-15'


def test_delete_countdown(page: Page):
    """Delete a specific countdown via button click, verify it's gone from DB."""
    countdown = _get_countdown_from_db('Birthday Party')
    countdown_id = countdown.id

    # Target the delete button in the specific countdown's form
    countdown_form = page.locator(f'form:has(input[name="id"][value="{countdown_id}"])')
    countdown_form.locator('button[value="delete"]').click()

    assert not _countdown_exists_in_db(countdown_id), 'Countdown should be deleted'


def test_countdown_create_and_delete_lifecycle(page: Page):
    """Create a countdown via the form, verify it appears, delete it, verify removal.

    Tests the full user flow: add via form at bottom of page, see it appear
    in the grid, then delete it and confirm it's gone from the database.
    """
    # Create
    form = page.locator('form.add-item-form')
    form.locator('#name').fill('Lifecycle Countdown')
    form.locator('#due_date').fill('2055-01-01')
    form.locator('#notes').fill('Full lifecycle test')
    form.locator('button[value="add"]').click()

    # Verify it was created in DB with correct fields
    countdown = _get_countdown_from_db('Lifecycle Countdown')
    countdown_id = countdown.id
    assert countdown.notes == 'Full lifecycle test'
    assert str(countdown.due_date) == '2055-01-01'

    # Verify it appears on the page
    expect(page.locator('h2', has_text='Lifecycle Countdown')).to_be_visible()

    # Delete it
    countdown_form = page.locator(f'form:has(input[name="id"][value="{countdown_id}"])')
    countdown_form.locator('button[value="delete"]').click()

    assert not _countdown_exists_in_db(countdown_id), 'Countdown should be deleted after lifecycle'
