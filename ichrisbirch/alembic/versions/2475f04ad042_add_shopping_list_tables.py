"""Add the shopping schema with sections, items and purchases.

Revision ID: 2475f04ad042
Revises: 816ce25c08dc
Create Date: 2026-10-10
"""

import sqlalchemy as sa
from alembic import op

revision = '2475f04ad042'
down_revision = '816ce25c08dc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE SCHEMA IF NOT EXISTS shopping')

    op.create_table(
        'sections',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('rank', sa.Double(), nullable=False),
        sa.Column('created_ts', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_sections'),
        schema='shopping',
    )
    op.create_index('uq_shopping_sections_name_folded', 'sections', [sa.text('lower(name)')], unique=True, schema='shopping')
    op.create_index('ix_shopping_sections_rank', 'sections', ['rank'], schema='shopping')

    op.create_table(
        'items',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('section_id', sa.Uuid(), nullable=True),
        sa.Column('rank', sa.Double(), nullable=False),
        sa.Column('is_needed', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('needed_ts', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_ts', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_items'),
        sa.ForeignKeyConstraint(['section_id'], ['shopping.sections.id'], name='fk_items_section_id_sections', ondelete='SET NULL'),
        schema='shopping',
    )
    op.create_index('uq_shopping_items_name_folded', 'items', [sa.text('lower(name)')], unique=True, schema='shopping')
    op.create_index('ix_shopping_items_section_id', 'items', ['section_id'], schema='shopping')
    op.create_index('ix_shopping_items_rank', 'items', ['rank'], schema='shopping')
    op.create_index('ix_shopping_items_is_needed', 'items', ['is_needed'], schema='shopping')

    op.create_table(
        'purchases',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('item_id', sa.Uuid(), nullable=True),
        sa.Column('item_name', sa.Text(), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('section_name', sa.Text(), nullable=True),
        sa.Column('purchased_ts', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_purchases'),
        sa.ForeignKeyConstraint(['item_id'], ['shopping.items.id'], name='fk_purchases_item_id_items', ondelete='SET NULL'),
        schema='shopping',
    )
    op.create_index('ix_shopping_purchases_item_id', 'purchases', ['item_id'], schema='shopping')
    op.create_index('ix_shopping_purchases_purchased_ts', 'purchases', ['purchased_ts'], schema='shopping')


def downgrade() -> None:
    op.drop_table('purchases', schema='shopping')
    op.drop_table('items', schema='shopping')
    op.drop_table('sections', schema='shopping')
    op.execute('DROP SCHEMA IF EXISTS shopping CASCADE')
