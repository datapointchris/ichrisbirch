"""Add review column to books

Revision ID: d1e2f3a4b5c6
Revises: c1a2b3d4e5f6
Create Date: 2026-03-15

"""

from alembic import op
import sqlalchemy as sa

revision = 'd1e2f3a4b5c6'
down_revision = 'c1a2b3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('books', sa.Column('review', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('books', 'review')
