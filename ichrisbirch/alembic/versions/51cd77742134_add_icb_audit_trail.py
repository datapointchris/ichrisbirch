"""add icb audit trail

Revision ID: 51cd77742134
Revises: 532aec322f58
Create Date: 2026-10-19 00:03:42.057025

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '51cd77742134'
down_revision = '532aec322f58'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'icb_audit_trail',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('table_name', sa.Text(), nullable=False),
        sa.Column('record_id', sa.Text(), nullable=False),
        sa.Column('operation', sa.Text(), nullable=False),
        sa.Column('changes', postgresql.JSONB(), nullable=False),
        sa.Column('actor', sa.Text(), nullable=True),
        sa.Column('request_id', sa.Text(), nullable=True),
        sa.Column('job_run_id', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_icb_audit_trail')),
        sa.CheckConstraint(
            "operation IN ('insert', 'update', 'delete')",
            name=op.f('ck_icb_audit_trail_operation_is_a_write'),
        ),
    )
    op.create_index('idx_icb_audit_trail_record', 'icb_audit_trail', ['table_name', 'record_id', 'changed_at'])
    op.create_index(op.f('ix_icb_audit_trail_changed_at'), 'icb_audit_trail', ['changed_at'])
    op.create_index(op.f('ix_icb_audit_trail_actor'), 'icb_audit_trail', ['actor'])


def downgrade() -> None:
    op.drop_table('icb_audit_trail')
