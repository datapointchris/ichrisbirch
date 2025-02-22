"""Require chat name unique, add created_on to chat and chatmessage tables.

Revision ID: 412471d3f20f
Revises: 01d40de7ea0e
Create Date: 2025-02-03 00:37:33.225845
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '412471d3f20f'
down_revision = '01d40de7ea0e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(op.f('uq_chats_name'), 'chats', ['name'], schema='chat')
    op.add_column(
        table_name='chats',
        column=sa.Column('created_on', sa.Date(), nullable=False, server_default=sa.text('CURRENT_DATE')),
        schema='chat',
    )
    op.add_column(
        table_name='messages',
        column=sa.Column('created_on', sa.Date(), nullable=False, server_default=sa.text('CURRENT_DATE')),
        schema='chat',
    )


def downgrade() -> None:
    op.drop_constraint(op.f('uq_chats_name'), 'chats', schema='chat')
    op.drop_column('chats', 'created_on', schema='chat')
    op.drop_column('messages', 'created_on', schema='chat')
