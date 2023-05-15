"""Change countdown `due_date` from datetime to date

Revision ID: d6c605cf75e1
Revises: cb0d2b146cda
Create Date: 2023-05-15 18:05:45.992110

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'd6c605cf75e1'
down_revision = 'cb0d2b146cda'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('countdowns', 'due_date', type_=sa.Date)


def downgrade() -> None:
    op.alter_column('countdowns', 'due_date', type_=sa.DateTime)
