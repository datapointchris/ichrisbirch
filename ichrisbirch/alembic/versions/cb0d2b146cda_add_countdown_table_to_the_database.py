"""Add countdown table to the database

Revision ID: cb0d2b146cda
Revises: 733fbc2709b9
Create Date: 2023-05-14 14:33:41.682515

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'cb0d2b146cda'
down_revision = '733fbc2709b9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('countdowns', sa.Column('notes', sa.Text(), nullable=True))
    op.add_column('countdowns', sa.Column('due_date', sa.DateTime(timezone=True), nullable=False))
    op.drop_column('countdowns', 'date')


def downgrade() -> None:
    op.add_column('countdowns', sa.Column('date', postgresql.TIMESTAMP(), autoincrement=False, nullable=False))
    op.drop_column('countdowns', 'due_date')
    op.drop_column('countdowns', 'notes')
