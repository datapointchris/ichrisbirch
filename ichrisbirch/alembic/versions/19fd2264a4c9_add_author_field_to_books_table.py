"""Add author field to books table.

Revision ID: 19fd2264a4c9
Revises: badfb24bd3d2
Create Date: 2024-12-21 13:25:50.042599
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '19fd2264a4c9'
down_revision = 'badfb24bd3d2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('books', sa.Column('author', sa.Text(), nullable=False))


def downgrade() -> None:
    op.drop_column('books', 'author')
