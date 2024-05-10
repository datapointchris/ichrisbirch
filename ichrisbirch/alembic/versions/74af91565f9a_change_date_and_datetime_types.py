"""Change date and datetime types.

Revision ID: 74af91565f9a
Revises: d6c605cf75e1
Create Date: 2023-06-27 23:10:22.277315
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '74af91565f9a'
down_revision = 'd6c605cf75e1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tasks
    op.alter_column('tasks', 'notes', existing_type=sa.VARCHAR(), type_=sa.Text(), nullable=True)

    # Events
    op.alter_column('events', 'date', existing_type=sa.DATE(), type_=sa.DateTime(timezone=True))


def downgrade() -> None:
    # Tasks
    op.alter_column('tasks', 'notes', existing_type=sa.Text(), type_=sa.VARCHAR(), nullable=True)

    # Events
    op.alter_column('events', 'date', existing_type=sa.DateTime(timezone=True), type_=sa.DATE())
