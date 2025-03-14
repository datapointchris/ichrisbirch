"""autotasks: add max_concurrent to table and model

Revision ID: a8839aab2b38
Revises: b6f0cf62ff57
Create Date: 2025-03-14 03:14:21.725524

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'a8839aab2b38'
down_revision = 'b6f0cf62ff57'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('autotasks', sa.Column('max_concurrent', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('autotasks', 'max_concurrent')
