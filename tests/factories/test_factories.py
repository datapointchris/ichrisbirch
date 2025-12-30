"""Tests for factory_boy factories.

These tests verify that the factories work correctly and demonstrate usage patterns.
"""

from datetime import UTC
from datetime import date
from datetime import datetime

from ichrisbirch.models.autotask import AutoTaskFrequency
from ichrisbirch.models.box import BoxSize
from ichrisbirch.models.task import TaskCategory

from . import ArticleFactory
from . import AutoTaskFactory
from . import BookFactory
from . import BoxFactory
from . import BoxItemFactory
from . import ChatFactory
from . import ChatMessageFactory
from . import CountdownFactory
from . import EventFactory
from . import HabitCategoryFactory
from . import HabitCompletedFactory
from . import HabitFactory
from . import MoneyWastedFactory
from . import TaskFactory
from . import UserFactory


class TestTaskFactory:
    """Test TaskFactory functionality."""

    def test_create_basic_task(self, factory_session):
        """Test creating a task with defaults."""
        task = TaskFactory()
        assert task.id is not None
        assert task.name.startswith('Test Task')
        assert task.category == TaskCategory.Chore
        assert task.complete_date is None

    def test_create_task_with_overrides(self, factory_session):
        """Test creating a task with specific values."""
        task = TaskFactory(
            name='Custom Task Name',
            category=TaskCategory.Home,
            priority=42,
        )
        assert task.name == 'Custom Task Name'
        assert task.category == TaskCategory.Home
        assert task.priority == 42

    def test_create_completed_task_with_trait(self, factory_session):
        """Test using the completed trait."""
        task = TaskFactory(completed=True)
        assert task.complete_date is not None
        assert isinstance(task.complete_date, datetime)

    def test_create_task_batch(self, factory_session):
        """Test creating multiple tasks."""
        tasks = TaskFactory.create_batch(3)
        assert len(tasks) == 3
        names = [t.name for t in tasks]
        assert len(set(names)) == 3

    def test_searchable_task(self, factory_session):
        """Test creating a task that matches a search term."""
        task = TaskFactory.searchable('urgent')
        assert 'urgent' in task.name.lower()
        assert 'urgent' in task.notes.lower()


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
        assert countdown.due_date > date.today()

    def test_past_due_countdown(self, factory_session):
        """Test creating a past due countdown."""
        countdown = CountdownFactory(past_due=True)
        assert countdown.due_date < date.today()

    def test_due_today_countdown(self, factory_session):
        """Test creating a countdown due today."""
        countdown = CountdownFactory(due_today=True)
        assert countdown.due_date == date.today()


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


class TestAutoTaskFactory:
    """Test AutoTaskFactory functionality."""

    def test_create_basic_autotask(self, factory_session):
        """Test creating an autotask with defaults."""
        autotask = AutoTaskFactory()
        assert autotask.id is not None
        assert autotask.name.startswith('Test AutoTask')
        assert autotask.frequency == AutoTaskFrequency.Weekly

    def test_daily_autotask(self, factory_session):
        """Test creating a daily autotask."""
        autotask = AutoTaskFactory(daily=True)
        assert autotask.frequency == AutoTaskFrequency.Daily

    def test_should_run_autotask(self, factory_session):
        """Test creating an autotask that should run."""
        autotask = AutoTaskFactory(should_run=True)
        # Last run was 30 days ago, so it should run
        assert autotask.should_run_today is True


class TestBookFactory:
    """Test BookFactory functionality."""

    def test_create_basic_book(self, factory_session):
        """Test creating a book with defaults."""
        book = BookFactory()
        assert book.id is not None
        assert book.title.startswith('Test Book')
        assert book.isbn is not None
        assert book.abandoned is False

    def test_reading_book(self, factory_session):
        """Test creating a book currently being read."""
        book = BookFactory(reading=True)
        assert book.read_start_date is not None
        assert book.read_finish_date is None

    def test_finished_book(self, factory_session):
        """Test creating a finished book."""
        book = BookFactory(finished=True)
        assert book.read_start_date is not None
        assert book.read_finish_date is not None
        assert book.rating is not None

    def test_abandoned_book(self, factory_session):
        """Test creating an abandoned book."""
        book = BookFactory(abandoned_book=True)
        assert book.abandoned is True


class TestEventFactory:
    """Test EventFactory functionality."""

    def test_create_basic_event(self, factory_session):
        """Test creating an event with defaults."""
        event = EventFactory()
        assert event.id is not None
        assert event.name.startswith('Test Event')
        assert event.attending is True
        assert event.date > datetime.now(UTC)

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
        assert event.date < datetime.now(UTC)


class TestBoxFactory:
    """Test BoxFactory functionality."""

    def test_create_basic_box(self, factory_session):
        """Test creating a box with defaults."""
        box = BoxFactory()
        assert box.id is not None
        assert box.name.startswith('Test Box')
        assert box.size == BoxSize.Medium
        assert box.essential is False

    def test_essential_box(self, factory_session):
        """Test creating an essential box."""
        box = BoxFactory(essential_box=True)
        assert box.essential is True

    def test_small_box(self, factory_session):
        """Test creating a small box."""
        box = BoxFactory(small=True)
        assert box.size == BoxSize.Small


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


class TestChatFactory:
    """Test ChatFactory functionality."""

    def test_create_basic_chat(self, factory_session):
        """Test creating a chat with defaults."""
        chat = ChatFactory()
        assert chat.id is not None
        assert chat.name.startswith('Test Chat')
        assert chat.category == 'General'

    def test_chat_with_subcategory(self, factory_session):
        """Test creating a chat with subcategory."""
        chat = ChatFactory(with_subcategory=True)
        assert chat.subcategory is not None


class TestChatMessageFactory:
    """Test ChatMessageFactory functionality."""

    def test_create_message_with_chat(self, factory_session):
        """Test creating a message with auto-generated chat."""
        message = ChatMessageFactory()
        assert message.id is not None
        assert message.chat is not None
        assert message.role == 'user'

    def test_assistant_message(self, factory_session):
        """Test creating an assistant message."""
        message = ChatMessageFactory(assistant=True)
        assert message.role == 'assistant'

    def test_message_in_specific_chat(self, factory_session):
        """Test creating messages in a specific chat."""
        chat = ChatFactory(name='Python Help')
        msg1 = ChatMessageFactory.user_message('How do I use decorators?', chat=chat)
        msg2 = ChatMessageFactory.assistant_message('Decorators are...', chat=chat)

        assert msg1.chat_id == chat.id
        assert msg2.chat_id == chat.id
        assert msg1.role == 'user'
        assert msg2.role == 'assistant'


class TestFactoryIntegration:
    """Integration tests showing real-world factory usage patterns."""

    def test_behavior_testing_pattern(self, factory_session):
        """Demonstrate behavior testing with explicit data."""
        home1 = TaskFactory(name='Integration Home Task 1', category=TaskCategory.Home)
        home2 = TaskFactory(name='Integration Home Task 2', category=TaskCategory.Home)
        TaskFactory(name='Integration Work Task', category=TaskCategory.Work)  # Creates non-Home task

        from sqlalchemy import select

        from ichrisbirch.models import Task

        home_tasks = (
            factory_session.execute(select(Task).where(Task.category == TaskCategory.Home, Task.name.like('Integration%'))).scalars().all()
        )

        assert len(home_tasks) == 2
        assert {t.id for t in home_tasks} == {home1.id, home2.id}

    def test_edge_case_testing(self, factory_session):
        """Demonstrate edge case testing."""
        task_empty = TaskFactory(name='')
        assert task_empty.name == ''

        task_long = TaskFactory(notes='x' * 5000)
        assert len(task_long.notes) == 5000

        task_negative = TaskFactory(priority=-10)
        assert task_negative.priority == -10

        task_zero = TaskFactory(priority=0)
        assert task_zero.priority == 0
