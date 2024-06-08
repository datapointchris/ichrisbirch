"""Add Articles table.

Revision ID: d34b7e1bd40d
Revises: 372bc2292a38
Create Date: 2024-06-05 16:54:08.207097
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd34b7e1bd40d'
down_revision = '372bc2292a38'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'articles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('save_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_read_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_count', sa.Integer(), nullable=False),
        sa.Column('is_favorite', sa.Boolean(), nullable=False),
        sa.Column('is_current', sa.Boolean(), nullable=False),
        sa.Column('is_archived', sa.Boolean(), nullable=False),
        sa.Column('review_days', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_articles_tags_array'), table_name='articles', columns=['tags'], postgresql_using='gin')


def downgrade() -> None:
    op.drop_index(op.f('ix_articles_tags_array'), table_name='articles')
    op.drop_table('articles')
