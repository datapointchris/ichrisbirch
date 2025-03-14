"""autotasks: set max_concurrent to 2 for all and make not nullable

Revision ID: e8cc676580bc
Revises: a8839aab2b38
Create Date: 2025-03-14 03:19:17.118580

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'e8cc676580bc'
down_revision = 'a8839aab2b38'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('UPDATE autotasks SET max_concurrent = 2')
    op.alter_column('autotasks', 'max_concurrent', existing_type=sa.Integer(), nullable=False)


def downgrade() -> None:
    op.alter_column('autotasks', 'max_concurrent', existing_type=sa.Integer(), nullable=True)
