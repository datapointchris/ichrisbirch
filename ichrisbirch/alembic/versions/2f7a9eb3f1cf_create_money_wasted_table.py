"""Create money_wasted table.

Revision ID: 2f7a9eb3f1cf
Revises: a38f5522f7c9
Create Date: 2024-07-31 23:45:30.600775
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '2f7a9eb3f1cf'
down_revision = 'a38f5522f7c9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'money_wasted',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('item', sa.String(length=64), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('date_purchased', sa.Date(), nullable=True),
        sa.Column('date_wasted', sa.Date(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('money_wasted')
