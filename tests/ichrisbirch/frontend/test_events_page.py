import pytest
from playwright.sync_api import Page
from playwright.sync_api import expect
from sqlalchemy import delete
from sqlalchemy import select

from ichrisbirch import models
from tests.factories import EventFactory
from tests.factories import clear_factory_session
from tests.factories import set_factory_session
from tests.ichrisbirch.frontend.fixtures import FRONTEND_BASE_URL
from tests.ichrisbirch.frontend.fixtures import login_regular_user
from tests.utils.database import create_session
from tests.utils.database import test_settings


@pytest.fixture(autouse=True)
def setup_test_events(insert_users_for_login):
    """Create test events using factories for this test module."""
    with create_session(test_settings) as session:
        set_factory_session(session)
        EventFactory(
            name='Concert Night',
            venue='The Fillmore',
            url='https://example.com/concert',
            cost=45.00,
            attending=True,
            notes='Bring earplugs',
        )
        EventFactory(
            name='Tech Meetup',
            venue='Convention Center',
            url='https://example.com/meetup',
            cost=0.00,
            attending=False,
            notes='Networking event',
        )
        EventFactory(
            name='Art Exhibition',
            venue='Downtown Gallery',
            url='https://example.com/art',
            cost=15.00,
            attending=False,
            notes=None,
        )
        session.commit()
        clear_factory_session()

    yield

    with create_session(test_settings) as session:
        session.execute(delete(models.Event))
        session.commit()


@pytest.fixture(autouse=True)
def login_homepage(setup_test_events, page: Page):
    login_regular_user(page)
    page.goto(f'{FRONTEND_BASE_URL}/events/')


def _get_event_from_db(name: str) -> models.Event:
    """Find an event by name via direct DB query."""
    with create_session(test_settings) as session:
        return session.execute(select(models.Event).where(models.Event.name == name)).scalar_one()


def _get_event_by_id_from_db(event_id: int) -> models.Event:
    """Get an event by ID via direct DB query."""
    with create_session(test_settings) as session:
        return session.execute(select(models.Event).where(models.Event.id == event_id)).scalar_one()


def _event_exists_in_db(event_id: int) -> bool:
    """Check if an event exists in DB."""
    with create_session(test_settings) as session:
        result = session.execute(select(models.Event).where(models.Event.id == event_id)).scalar_one_or_none()
        return result is not None


def test_events_index(page: Page):
    expect(page).to_have_title('Events')
    # All 3 events should be visible
    expect(page.locator('.grid__item h2')).to_have_count(3)


def test_create_event(page: Page):
    """Fill the add form in a real browser, submit, verify in DB."""
    form = page.locator('form.add-item-form')
    form.locator('#name').fill('Playwright Event')
    form.locator('#date').fill('2051-07-04T19:00')
    form.locator('#venue').fill('Playwright Theater')
    form.locator('#url').fill('https://example.com/playwright-event')
    form.locator('#cost').fill('99.50')
    form.locator('#attending').check()
    form.locator('#notes').fill('Created by Playwright')
    form.locator('button[value="add"]').click()

    event = _get_event_from_db('Playwright Event')
    assert event.venue == 'Playwright Theater'
    assert event.url == 'https://example.com/playwright-event'
    assert event.cost == 99.50
    assert event.attending is True
    assert event.notes == 'Created by Playwright'


def test_create_event_not_attending(page: Page):
    """Create an event without checking attending — hidden input should send '0'."""
    form = page.locator('form.add-item-form')
    form.locator('#name').fill('Skip This One')
    form.locator('#date').fill('2051-08-01T12:00')
    form.locator('#venue').fill('Somewhere')
    form.locator('#cost').fill('10')
    form.locator('button[value="add"]').click()

    event = _get_event_from_db('Skip This One')
    assert event.attending is not True, 'Unchecked attending should be False'


def test_attend_event(page: Page):
    """Click attend on a non-attending event, verify state change in DB."""
    event = _get_event_from_db('Tech Meetup')
    event_id = event.id
    assert event.attending is False

    # The attend button is in a form with the event's hidden id
    event_form = page.locator(f'form:has(input[name="id"][value="{event_id}"]):has(button[value="attend"])')
    event_form.locator('button[value="attend"]').click()

    result = _get_event_by_id_from_db(event_id)
    assert result.attending is True, 'Event should now be attending'
    assert result.venue == 'Convention Center', 'Other fields should survive'


def test_delete_event(page: Page):
    """Delete a specific event via button click, verify it's gone from DB."""
    event = _get_event_from_db('Art Exhibition')
    event_id = event.id

    event_form = page.locator(f'form:has(input[name="id"][value="{event_id}"]):has(button[value="delete"])')
    event_form.locator('button[value="delete"]').click()

    assert not _event_exists_in_db(event_id), 'Event should be deleted'


def test_event_create_attend_delete_lifecycle(page: Page):
    """Create an event not attending, attend it, then delete it.

    Tests state accumulation across multiple actions on the same event.
    """
    # Create
    form = page.locator('form.add-item-form')
    form.locator('#name').fill('Lifecycle Event')
    form.locator('#date').fill('2052-01-01T20:00')
    form.locator('#venue').fill('Lifecycle Venue')
    form.locator('#cost').fill('0')
    form.locator('button[value="add"]').click()

    event = _get_event_from_db('Lifecycle Event')
    event_id = event.id
    assert event.attending is not True

    # Attend
    attend_form = page.locator(f'form:has(input[name="id"][value="{event_id}"]):has(button[value="attend"])')
    attend_form.locator('button[value="attend"]').click()

    result = _get_event_by_id_from_db(event_id)
    assert result.attending is True
    assert result.venue == 'Lifecycle Venue', 'Venue should survive attend'

    # Delete
    delete_form = page.locator(f'form:has(input[name="id"][value="{event_id}"]):has(button[value="delete"])')
    delete_form.locator('button[value="delete"]').click()

    assert not _event_exists_in_db(event_id), 'Event should be deleted after lifecycle'
