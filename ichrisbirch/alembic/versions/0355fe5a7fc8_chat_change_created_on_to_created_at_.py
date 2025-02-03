"""chat: change created_on to created_at, date to datetime, for ordering

Revision ID: 0355fe5a7fc8
Revises: 412471d3f20f
Create Date: 2025-02-03 11:23:34.384285
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '0355fe5a7fc8'
down_revision = '412471d3f20f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        table_name='chats',
        column_name='created_on',
        new_column_name='created_at',
        type_=sa.DateTime(timezone=True),
        schema='chat',
    )
    op.alter_column(
        table_name='messages',
        column_name='created_on',
        new_column_name='created_at',
        type_=sa.DateTime(timezone=True),
        schema='chat',
    )


def downgrade() -> None:
    op.alter_column(
        table_name='chats',
        column_name='created_at',
        new_column_name='created_on',
        type_=sa.Date,
        schema='chat',
    )
    op.alter_column(
        table_name='messages',
        column_name='created_at',
        new_column_name='created_on',
        type_=sa.Date,
        schema='chat',
    )
