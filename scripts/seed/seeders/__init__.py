"""Seed modules and execution order."""

from __future__ import annotations

import types

from scripts.seed.seeders import articles
from scripts.seed.seeders import autotasks
from scripts.seed.seeders import books
from scripts.seed.seeders import boxes
from scripts.seed.seeders import chats
from scripts.seed.seeders import countdowns
from scripts.seed.seeders import durations
from scripts.seed.seeders import events
from scripts.seed.seeders import habits
from scripts.seed.seeders import money_wasted
from scripts.seed.seeders import projects
from scripts.seed.seeders import tasks

# Parents before children, independent models first
SEED_ORDER: list[tuple[str, types.ModuleType]] = [
    ('tasks', tasks),
    ('habits', habits),
    ('books', books),
    ('articles', articles),
    ('events', events),
    ('countdowns', countdowns),
    ('autotasks', autotasks),
    ('money_wasted', money_wasted),
    ('durations', durations),
    ('boxes', boxes),
    ('chats', chats),
    ('projects', projects),
]
