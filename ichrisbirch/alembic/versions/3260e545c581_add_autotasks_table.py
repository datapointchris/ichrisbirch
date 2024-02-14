"""Add autotasks table

Revision ID: 3260e545c581
Revises: 0bc20d6a3ae1
Create Date: 2023-05-03 21:10:02.819787

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from ichrisbirch.models.autotask import TaskFrequency
from ichrisbirch.models.task import TaskCategory

# revision identifiers, used by Alembic.
revision = '3260e545c581'
down_revision = '0bc20d6a3ae1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    category_enum = postgresql.ENUM(TaskCategory, name='TaskCategory')
    frequency_enum = postgresql.ENUM(TaskFrequency, name='TaskFrequency')
    op.create_table(
        'autotasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('category', category_enum, nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_run_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('frequency', frequency_enum, nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('autotasks')
