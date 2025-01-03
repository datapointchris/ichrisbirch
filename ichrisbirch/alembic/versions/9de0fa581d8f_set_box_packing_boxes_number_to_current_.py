"""Set box_packing.boxes.number to current id for all boxes.

Revision ID: 9de0fa581d8f
Revises: be539ad0dd27
Create Date: 2025-01-02 19:57:29.497572
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '9de0fa581d8f'
down_revision = 'be539ad0dd27'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE box_packing.boxes
        SET number = id
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE box_packing.boxes
        SET number = NULL
        """
    )
