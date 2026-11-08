"""Add autofun and autofun_active_tasks tables.

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-04-02
"""

from alembic import op
import sqlalchemy as sa

revision = 'f2a3b4c5d6e7'
down_revision = 'e1f2a3b4c5d6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'autofun',
        sa.Column('id', sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('completed_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('added_date', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'autofun_active_tasks',
        sa.Column('fun_item_id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['fun_item_id'], ['autofun.id']),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id']),
        sa.PrimaryKeyConstraint('fun_item_id', 'task_id'),
    )


def downgrade() -> None:
    op.drop_table('autofun_active_tasks')
    op.drop_table('autofun')
