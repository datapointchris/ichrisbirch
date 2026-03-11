"""add article_failed_imports table

Revision ID: f7c621995378
Revises: a3b7c9d1e4f2
Create Date: 2026-03-11 03:02:51.641225

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f7c621995378'
down_revision = 'a3b7c9d1e4f2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'article_failed_imports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('batch_id', sa.String(length=36), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_article_failed_imports')),
    )


def downgrade() -> None:
    op.drop_table('article_failed_imports')
