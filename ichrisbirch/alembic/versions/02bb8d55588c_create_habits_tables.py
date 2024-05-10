"""Create habits tables.

Revision ID: 02bb8d55588c
Revises: 6d0ab5ffd636
Create Date: 2024-04-27 00:05:43.707829
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '02bb8d55588c'
down_revision = '6d0ab5ffd636'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('is_current', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='habits',
    )

    op.create_table(
        'completed',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('complete_date', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ['category_id'],
            ['habits.categories.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
        schema='habits',
    )
    op.create_table(
        'habits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('is_current', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ['category_id'],
            ['habits.categories.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
        schema='habits',
    )


def downgrade() -> None:
    op.drop_table('habits', schema='habits')
    op.drop_table('completed', schema='habits')
    op.drop_table('categories', schema='habits')
