"""Add durations and duration_notes tables.

Revision ID: a1b2c3d4e5f6
Revises: f7c621995378
Create Date: 2026-03-13 16:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'f7c621995378'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'durations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'duration_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('duration_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['duration_id'], ['durations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('duration_notes')
    op.drop_table('durations')
