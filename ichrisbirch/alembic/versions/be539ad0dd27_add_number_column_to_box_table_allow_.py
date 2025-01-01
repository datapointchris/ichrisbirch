"""Add number column to box table, allow missing foreign key boxitem.

Revision ID: be539ad0dd27
Revises: 19fd2264a4c9
Create Date: 2025-01-01 01:27:04.737007
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'be539ad0dd27'
down_revision = '19fd2264a4c9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(table_name='boxes', column=sa.Column('number', sa.Integer(), nullable=True), schema='box_packing')
    op.alter_column(table_name='items', column_name='box_id', nullable=True, schema='box_packing')
    op.drop_constraint(
        constraint_name='items_box_id_fkey',
        table_name='items',
        type_='foreignkey',
        schema='box_packing',
    )
    op.create_foreign_key(
        constraint_name='fk_box_packing_items_box_id_box_packing_boxes',
        source_table='items',
        referent_table='boxes',
        local_cols=['box_id'],
        remote_cols=['id'],
        ondelete='SET NULL',
        source_schema='box_packing',
        referent_schema='box_packing',
    )


def downgrade() -> None:
    op.alter_column(table_name='items', column_name='box_id', nullable=False, schema='box_packing')
    op.drop_column(table_name='boxes', column_name='number', schema='box_packing')
    op.drop_constraint(
        constraint_name='fk_box_packing_items_box_id_box_packing_boxes',
        table_name='items',
        type_='foreignkey',
        schema='box_packing',
    )
    op.create_foreign_key(
        constraint_name='items_box_id_fkey',
        source_table='items',
        referent_table='boxes',
        local_cols=['box_id'],
        remote_cols=['id'],
        source_schema='box_packing',
        referent_schema='box_packing',
    )
