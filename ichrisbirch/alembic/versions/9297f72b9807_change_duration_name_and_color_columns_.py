"""change duration name and color columns to text

Revision ID: 9297f72b9807
Revises: a1b2c3d4e5f6
Create Date: 2026-03-13 17:35:17.105797

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9297f72b9807'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('durations', 'name', type_=sa.Text(), existing_type=sa.String(128))
    op.alter_column('durations', 'color', type_=sa.Text(), existing_type=sa.String(7))


def downgrade() -> None:
    op.alter_column('durations', 'name', type_=sa.String(128), existing_type=sa.Text())
    op.alter_column('durations', 'color', type_=sa.String(7), existing_type=sa.Text())
