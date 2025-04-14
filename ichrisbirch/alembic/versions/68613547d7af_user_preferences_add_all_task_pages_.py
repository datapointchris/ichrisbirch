"""user preferences: add all task pages views

Revision ID: 68613547d7af
Revises: 370978067d9d
Create Date: 2025-04-14 03:26:17.435979

"""

from alembic import op

from ichrisbirch.database.sqlalchemy.session import SessionLocal
from ichrisbirch.models.user import DEFAULT_USER_PREFERENCES
from scripts.update_user_preferences_migration import migrate_preferences

# revision identifiers, used by Alembic.
revision = '68613547d7af'
down_revision = '370978067d9d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    with SessionLocal(bind=bind) as session:
        migrate_preferences(session, default_preferences=DEFAULT_USER_PREFERENCES)


def downgrade() -> None:
    # No real downgrade as this is trying to fix missing preferences
    bind = op.get_bind()
    with SessionLocal(bind=bind) as session:
        migrate_preferences(session, default_preferences=DEFAULT_USER_PREFERENCES)
