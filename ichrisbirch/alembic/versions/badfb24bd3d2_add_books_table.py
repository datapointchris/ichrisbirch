"""Add books table.

Revision ID: badfb24bd3d2
Revises: 580059210a03
Create Date: 2024-12-04 00:17:08.097247
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'badfb24bd3d2'
down_revision = '580059210a03'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'books',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('isbn', sa.Text(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('tags', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('goodreads_url', sa.Text(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('purchase_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('purchase_price', sa.Float(), nullable=True),
        sa.Column('sell_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sell_price', sa.Float(), nullable=True),
        sa.Column('read_start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_finish_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('abandoned', sa.Boolean(), nullable=True),
        sa.Column('location', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('isbn'),
    )


def downgrade() -> None:
    op.drop_table('books')
