"""Add job_run_id correlation column to scheduler_job_runs

Revision ID: d5e6f7a8b9c0
Revises: c5d6e7f8a9b0
Create Date: 2026-04-24

"""

import sqlalchemy as sa
from alembic import op

revision = 'd5e6f7a8b9c0'
down_revision = 'c5d6e7f8a9b0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'scheduler_job_runs',
        sa.Column('job_run_id', sa.Text(), nullable=True),
        schema='admin',
    )
    op.create_index(
        'ix_scheduler_job_runs_job_run_id',
        'scheduler_job_runs',
        ['job_run_id'],
        schema='admin',
    )


def downgrade() -> None:
    op.drop_index('ix_scheduler_job_runs_job_run_id', 'scheduler_job_runs', schema='admin')
    op.drop_column('scheduler_job_runs', 'job_run_id', schema='admin')
