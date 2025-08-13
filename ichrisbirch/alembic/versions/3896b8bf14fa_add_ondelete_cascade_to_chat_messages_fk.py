"""Add ondelete cascade to chat messages FK.

Revision ID: 3896b8bf14fa
Revises: aee90d6dde57
Create Date: 2025-04-21 00:57:01.401993
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '3896b8bf14fa'
down_revision = '68613547d7af'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint('fk_messages_chat_id_chats', 'messages', schema='chat', type_='foreignkey')
    op.create_foreign_key(
        'fk_messages_chat_id_chats',
        'messages',
        'chats',
        ['chat_id'],
        ['id'],
        source_schema='chat',
        referent_schema='chat',
        ondelete='CASCADE',
    )


def downgrade() -> None:
    op.drop_constraint('fk_messages_chat_id_chats', 'messages', schema='chat', type_='foreignkey')
    op.create_foreign_key(
        'fk_messages_chat_id_chats',
        'messages',
        'chats',
        ['chat_id'],
        ['id'],
        source_schema='chat',
        referent_schema='chat',
    )
