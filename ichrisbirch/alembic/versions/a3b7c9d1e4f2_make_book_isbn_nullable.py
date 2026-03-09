"""make book isbn nullable

Revision ID: a3b7c9d1e4f2
Revises: 6c8f9a0ef2cd
Create Date: 2026-03-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3b7c9d1e4f2'
down_revision = '6c8f9a0ef2cd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('books', 'isbn', existing_type=sa.Text(), nullable=True)


def downgrade() -> None:
    op.alter_column('books', 'isbn', existing_type=sa.Text(), nullable=False)
