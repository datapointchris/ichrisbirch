"""Add notes column to tasks table

Revision ID: c119daabf840
Revises: 0f98f2e006f5
Create Date: 2022-12-31 00:35:59.776047

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'c119daabf840'
down_revision = '0f98f2e006f5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('tasks', sa.Column('notes', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('tasks', sa.Column('notes', sa.String(), nullable=True))
