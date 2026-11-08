"""add patterns table

Revision ID: 87fb375b2531
Revises: b8c9d0e1f2a3
Create Date: 2026-08-07 16:00:21.671497

Autogenerate also proposed dropping the apartments schema, portfolio and
journal, and rewriting four unrelated indexes — pre-existing drift between the
dev database and the models, not part of this change. Only the patterns table
is kept here.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '87fb375b2531'
down_revision = 'b8c9d0e1f2a3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'patterns',
        sa.Column('id', sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_patterns')),
    )


def downgrade() -> None:
    op.drop_table('patterns')
