"""Add and rename a column in autotasks table.

Revision ID: 733fbc2709b9
Revises: 3260e545c581
Create Date: 2023-05-04 00:00:01.349913
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '733fbc2709b9'
down_revision = '3260e545c581'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('autotasks', sa.Column('run_count', sa.Integer, server_default='0', nullable=False))
    op.alter_column('autotasks', 'start_date', new_column_name='first_run_date')


def downgrade() -> None:
    op.drop_column('autotasks', 'first_run_date')
    op.alter_column('autotasks', 'last_run_date', new_column_name='start_date')
