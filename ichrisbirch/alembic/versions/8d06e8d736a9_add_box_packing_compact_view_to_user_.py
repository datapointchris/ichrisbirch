"""Add box_packing.compact_view to user preferences.

Revision ID: 8d06e8d736a9
Revises: 9de0fa581d8f
Create Date: 2025-01-08 15:07:42.999292
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '8d06e8d736a9'
down_revision = '9de0fa581d8f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE users
        SET preferences = jsonb_insert(
            preferences::jsonb,
            '{box_packing}',
            '{"compact_view": true}'::jsonb,
            true
        );
    """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE users
        SET preferences = preferences #- '{box_packing,compact_view}'
    """
    )
