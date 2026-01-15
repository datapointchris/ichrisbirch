"""fix column sizes use text for postgres_version and email

Revision ID: ebb7845c26d9
Revises: 2e7c160befcf
Create Date: 2026-01-15 20:23:24.119546

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ebb7845c26d9'
down_revision = '2e7c160befcf'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Fix postgres_version column - use TEXT per PostgreSQL best practice
    # Previous String(50) was too small for full version strings (~90 chars)
    op.alter_column(
        'backup_history',
        'postgres_version',
        type_=sa.Text(),
        existing_type=sa.String(length=50),
        schema='admin',
    )
    # Fix email column - use TEXT for flexibility
    # Previous String(40) was too restrictive (RFC 5321 allows up to 254 chars)
    op.alter_column(
        'users',
        'email',
        type_=sa.Text(),
        existing_type=sa.String(length=40),
    )


def downgrade() -> None:
    op.alter_column(
        'backup_history',
        'postgres_version',
        type_=sa.String(length=50),
        existing_type=sa.Text(),
        schema='admin',
    )
    op.alter_column(
        'users',
        'email',
        type_=sa.String(length=40),
        existing_type=sa.Text(),
    )
