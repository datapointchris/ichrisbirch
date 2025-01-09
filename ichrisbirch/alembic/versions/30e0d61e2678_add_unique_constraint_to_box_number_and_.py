"""Add unique constraint to box.number and not nullable.

Revision ID: 30e0d61e2678
Revises: 8d06e8d736a9
Create Date: 2025-01-08 23:05:54.101333
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '30e0d61e2678'
down_revision = '8d06e8d736a9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(table_name='boxes', column_name='number', schema='box_packing', nullable=False)
    op.create_unique_constraint(constraint_name=None, table_name='boxes', columns=['number'], schema='box_packing')


def downgrade() -> None:
    op.drop_constraint(constraint_name='uq_boxes_number', table_name='boxes', type_='unique', schema='box_packing')
    op.alter_column(table_name='boxes', column_name='number', schema='box_packing', nullable=True)
