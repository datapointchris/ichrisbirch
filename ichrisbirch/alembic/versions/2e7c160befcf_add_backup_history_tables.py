"""add backup history tables

Revision ID: 2e7c160befcf
Revises: 3896b8bf14fa
Create Date: 2026-01-15 14:53:25.240130

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2e7c160befcf'
down_revision = '3896b8bf14fa'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create admin schema if it doesn't exist
    op.execute('CREATE SCHEMA IF NOT EXISTS admin')

    op.create_table('backup_history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('description', sa.String(length=100), nullable=False),
    sa.Column('backup_type', sa.String(length=20), nullable=False),
    sa.Column('environment', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('size_bytes', sa.BigInteger(), nullable=True),
    sa.Column('duration_seconds', sa.Float(), nullable=True),
    sa.Column('s3_key', sa.String(length=500), nullable=True),
    sa.Column('local_path', sa.String(length=500), nullable=True),
    sa.Column('success', sa.Boolean(), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('table_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('postgres_version', sa.String(length=50), nullable=True),
    sa.Column('database_size_bytes', sa.BigInteger(), nullable=True),
    sa.Column('checksum', sa.String(length=64), nullable=True),
    sa.Column('triggered_by_user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['triggered_by_user_id'], ['users.id'], name=op.f('fk_backup_history_triggered_by_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_backup_history')),
    sa.UniqueConstraint('filename', name=op.f('uq_backup_history_filename')),
    schema='admin'
    )
    op.create_table('backup_restores',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('backup_id', sa.Integer(), nullable=False),
    sa.Column('restored_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('restored_to_environment', sa.String(length=20), nullable=False),
    sa.Column('duration_seconds', sa.Float(), nullable=True),
    sa.Column('success', sa.Boolean(), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('restored_by_user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['backup_id'], ['admin.backup_history.id'], name=op.f('fk_backup_restores_backup_id_backup_history')),
    sa.ForeignKeyConstraint(['restored_by_user_id'], ['users.id'], name=op.f('fk_backup_restores_restored_by_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_backup_restores')),
    schema='admin'
    )


def downgrade() -> None:
    op.drop_table('backup_restores', schema='admin')
    op.drop_table('backup_history', schema='admin')
    op.execute('DROP SCHEMA IF EXISTS admin')
