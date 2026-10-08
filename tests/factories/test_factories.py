"""Tests for factory_boy factories.

These tests verify that the factories work correctly and demonstrate usage patterns.
"""

import datetime as dt
from zoneinfo import ZoneInfo

from . import ArticleFactory
from . import BookFactory
from . import BoxFactory
from . import BoxItemFactory
from . import CountdownFactory
from . import EventFactory
from . import HabitCategoryFactory
from . import HabitCompletedFactory
from . import HabitFactory
from . import MoneyWastedFactory
from . import UserFactory


class TestUserFactory:
    """Test UserFactory functionality."""

    def test_create_basic_user(self, factory_session):
        """Test creating a user with defaults."""
        user = UserFactory()
        assert user.id is not None
        assert user.name.startswith('Test User')
        assert user.email.startswith('testuser')
        assert user.is_admin is False

    def test_create_admin_user(self, factory_session):
        """Test creating an admin user with trait."""
        admin = UserFactory(admin=True)
        assert admin.is_admin is True

    def test_password_is_hashed(self, factory_session):
        """Test that password is hashed on insert."""
        user = UserFactory(password='mypassword')
        assert user.password != 'mypassword'
        assert user.check_password('mypassword')

    def test_unique_emails(self, factory_session):
        """Test that batch users have unique emails."""
        users = UserFactory.create_batch(3)
        emails = [u.email for u in users]
        assert len(set(emails)) == 3


class TestHabitFactory:
    """Test HabitFactory functionality."""

    def test_create_habit_with_category(self, factory_session):
        """Test that habits are created with a category."""
        habit = HabitFactory()
        assert habit.id is not None
        assert habit.category is not None
        assert habit.category_id is not None
        assert habit.is_current is True

    def test_create_habit_with_existing_category(self, factory_session):
        """Test creating habits that share a category."""
        category = HabitCategoryFactory(name='Shared Category')
        habit1 = HabitFactory(category=category)
        habit2 = HabitFactory(category=category)

        assert habit1.category_id == habit2.category_id
        assert habit1.category.name == 'Shared Category'

    def test_hibernated_habit(self, factory_session):
        """Test creating a hibernated habit."""
        habit = HabitFactory(hibernated=True)
        assert habit.is_current is False

    def test_habit_with_hibernated_category(self, factory_session):
        """Test creating a habit with a hibernated category."""
        habit = HabitFactory(with_hibernated_category=True)
        assert habit.category.is_current is False


class TestHabitCategoryFactory:
    """Test HabitCategoryFactory functionality."""

    def test_create_basic_category(self, factory_session):
        """Test creating a category with defaults."""
        category = HabitCategoryFactory()
        assert category.id is not None
        assert category.name.startswith('Test Category')
        assert category.is_current is True

    def test_hibernated_category(self, factory_session):
        """Test creating a hibernated category."""
        category = HabitCategoryFactory(hibernated=True)
        assert category.is_current is False


class TestHabitCompletedFactory:
    """Test HabitCompletedFactory functionality."""

    def test_create_completed_habit(self, factory_session):
        """Test creating a completed habit record."""
        completed = HabitCompletedFactory()
        assert completed.id is not None
        assert completed.name.startswith('Completed Habit')
        assert completed.complete_date is not None
        assert completed.category is not None

    def test_completed_habit_with_existing_category(self, factory_session):
        """Test creating a completed habit with existing category."""
        category = HabitCategoryFactory(name='Exercise')
        completed = HabitCompletedFactory.with_category(category)
        assert completed.category.name == 'Exercise'


class TestCountdownFactory:
    """Test CountdownFactory functionality."""

    def test_create_basic_countdown(self, factory_session):
        """Test creating a countdown with defaults."""
        countdown = CountdownFactory()
        assert countdown.id is not None
        assert countdown.name.startswith('Test Countdown')
        assert countdown.due_date > dt.date.today()

    def test_past_due_countdown(self, factory_session):
        """Test creating a past due countdown."""
        countdown = CountdownFactory(past_due=True)
        assert countdown.due_date < dt.date.today()

    def test_due_today_countdown(self, factory_session):
        """Test creating a countdown due today."""
        countdown = CountdownFactory(due_today=True)
        assert countdown.due_date == dt.date.today()


class TestMoneyWastedFactory:
    """Test MoneyWastedFactory functionality."""

    def test_create_basic_money_wasted(self, factory_session):
        """Test creating a money wasted entry."""
        entry = MoneyWastedFactory()
        assert entry.id is not None
        assert entry.item.startswith('Wasted Item')
        assert entry.amount > 0

    def test_expensive_item(self, factory_session):
        """Test creating an expensive wasted item."""
        entry = MoneyWastedFactory(expensive=True)
        assert entry.amount == 500.0


class TestBookFactory:
    """Test BookFactory functionality."""

    def test_create_basic_book(self, factory_session):
        """Test creating a book with defaults."""
        book = BookFactory()
        assert book.id is not None
        assert book.title.startswith('Test Book')
        assert book.isbn is not None
        assert book.progress == 'unread'

    def test_reading_book(self, factory_session):
        """Test creating a book currently being read."""
        book = BookFactory(reading=True)
        assert book.read_start_date is not None
        assert book.read_finish_date is None
        assert book.progress == 'reading'

    def test_finished_book(self, factory_session):
        """Test creating a finished book."""
        book = BookFactory(finished=True)
        assert book.read_start_date is not None
        assert book.read_finish_date is not None
        assert book.rating is not None
        assert book.progress == 'read'

    def test_abandoned_book(self, factory_session):
        """Test creating an abandoned book."""
        book = BookFactory(abandoned_book=True)
        assert book.progress == 'abandoned'


class TestEventFactory:
    """Test EventFactory functionality."""

    def test_create_basic_event(self, factory_session):
        """Test creating an event with defaults."""
        event = EventFactory()
        assert event.id is not None
        assert event.name.startswith('Test Event')
        assert event.attending is True
        # date is a reading on a clock at the venue, so it carries no offset and has
        # to be resolved against its own zone before it means an instant.
        assert event.date.tzinfo is None
        assert event.date.replace(tzinfo=ZoneInfo(event.timezone)) > dt.datetime.now(dt.UTC)

    def test_not_attending_event(self, factory_session):
        """Test creating an event not attending."""
        event = EventFactory(not_attending=True)
        assert event.attending is False

    def test_free_event(self, factory_session):
        """Test creating a free event."""
        event = EventFactory(free=True)
        assert event.cost == 0.0

    def test_past_event(self, factory_session):
        """Test creating a past event."""
        event = EventFactory(past=True)
        assert event.date < dt.datetime.now(dt.UTC)


class TestBoxFactory:
    """Test BoxFactory functionality."""

    def test_create_basic_box(self, factory_session):
        """Test creating a box with defaults."""
        box = BoxFactory()
        assert box.id is not None
        assert box.name.startswith('Test Box')
        assert box.size == 'Medium'
        assert box.essential is False

    def test_essential_box(self, factory_session):
        """Test creating an essential box."""
        box = BoxFactory(essential_box=True)
        assert box.essential is True

    def test_small_box(self, factory_session):
        """Test creating a small box."""
        box = BoxFactory(small=True)
        assert box.size == 'Small'


class TestBoxItemFactory:
    """Test BoxItemFactory functionality."""

    def test_create_item_with_box(self, factory_session):
        """Test creating an item with auto-generated box."""
        item = BoxItemFactory()
        assert item.id is not None
        assert item.box is not None
        assert item.box_id is not None

    def test_create_orphan_item(self, factory_session):
        """Test creating an item without a box."""
        item = BoxItemFactory(orphan=True)
        assert item.box is None
        assert item.box_id is None

    def test_create_item_in_specific_box(self, factory_session):
        """Test creating items in a specific box."""
        box = BoxFactory(name='Kitchen Box')
        item1 = BoxItemFactory.in_box(box, name='Plates')
        item2 = BoxItemFactory.in_box(box, name='Cups')

        assert item1.box_id == box.id
        assert item2.box_id == box.id


class TestArticleFactory:
    """Test ArticleFactory functionality."""

    def test_create_basic_article(self, factory_session):
        """Test creating an article with defaults."""
        article = ArticleFactory()
        assert article.id is not None
        assert article.title.startswith('Test Article')
        assert article.is_current is True
        assert article.is_archived is False

    def test_favorite_article(self, factory_session):
        """Test creating a favorite article."""
        article = ArticleFactory(favorite=True)
        assert article.is_favorite is True

    def test_archived_article(self, factory_session):
        """Test creating an archived article."""
        article = ArticleFactory(archived=True)
        assert article.is_archived is True
        assert article.is_current is False

    def test_read_article(self, factory_session):
        """Test creating a read article."""
        article = ArticleFactory(read=True)
        assert article.last_read_date is not None
        assert article.read_count == 1
