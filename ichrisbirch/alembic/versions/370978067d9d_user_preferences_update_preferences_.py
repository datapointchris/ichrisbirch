"""user preferences: update preferences with nested defaults

Revision ID: 370978067d9d
Revises: bb9555ffa490
Create Date: 2025-04-14 02:46:45.315349

"""

from alembic import op

from ichrisbirch.database.session import create_session
from ichrisbirch.models.user import DEFAULT_USER_PREFERENCES
from scripts.update_user_preferences_migration import migrate_preferences

# revision identifiers, used by Alembic.
revision = '370978067d9d'
down_revision = 'bb9555ffa490'
branch_labels = None
depends_on = None


def upgrade() -> None:
    transfer_map = {'theme': 'theme_color'}
    bind = op.get_bind()
    with create_session() as session:
        migrate_preferences(session, default_preferences=DEFAULT_USER_PREFERENCES, transfer_map=transfer_map)


BEFORE_PREFERENCES = {
    'theme': 'turquoise',
    'dark_mode': True,
    'notifications': False,
    'dashboard_layout': [
        ['tasks_priority', 'countdowns', 'events'],
        ['habits', 'brainlog', 'devlog'],
    ],
}


def downgrade() -> None:
    transfer_map = {'theme_color': 'theme'}
    bind = op.get_bind()
    with create_session() as session:
        migrate_preferences(session, default_preferences=BEFORE_PREFERENCES, transfer_map=transfer_map)
