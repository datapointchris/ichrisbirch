"""Create chat.chats and chat.messages tables

Revision ID: 01d40de7ea0e
Revises: 30e0d61e2678
Create Date: 2025-02-02 21:14:59.859029
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '01d40de7ea0e'
down_revision = '30e0d61e2678'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE SCHEMA IF NOT EXISTS chat')
    op.create_table(
        'chats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('category', sa.Text(), nullable=True),
        sa.Column('subcategory', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_chats')),
        schema='chat',
    )
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chat_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.Text(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['chat_id'], ['chat.chats.id'], name=op.f('fk_messages_chat_id_chats')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_messages')),
        schema='chat',
    )


def downgrade() -> None:
    op.drop_table('chats', schema='chat')
    op.drop_table('messages', schema='chat')
    op.execute('DROP SCHEMA IF EXISTS chat CASCADE')
