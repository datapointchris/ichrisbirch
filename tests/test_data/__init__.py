from tests.test_data import articles
from tests.test_data import autotasks
from tests.test_data import books
from tests.test_data import boxes
from tests.test_data import chats
from tests.test_data import countdowns
from tests.test_data import events
from tests.test_data import habitcategories
from tests.test_data import money_wasted
from tests.test_data import scheduler
from tests.test_data import tasks
from tests.test_data import users

__all__ = [
    'articles',
    'autotasks',
    'books',
    'boxes',
    # 'boxitems' - now inserted via Box.items relationship
    'chats',
    'countdowns',
    'events',
    'habitcategories',
    # 'habits' - now inserted via HabitCategory.habits relationship
    # 'habitscompleted' - now inserted via HabitCategory.completed_habits relationship
    'money_wasted',
    'scheduler',
    'tasks',
    'users',
]
