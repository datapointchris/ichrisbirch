"""drop article_failed_imports

A bulk import's failure lives in its batch's status for the 24 hours the batch
is kept, and nowhere else. The release before this one stopped reading and
writing the table, so the color it leaves serving is safe once it is gone.

Revision ID: 532aec322f58
Revises: a0c4a2393384
Create Date: 2026-10-10 18:55:33.209950

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '532aec322f58'
down_revision = 'a0c4a2393384'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table('article_failed_imports')


def downgrade() -> None:
    # Rebuilds the table empty; the rows the upgrade dropped do not come back.
    op.create_table(
        'article_failed_imports',
        sa.Column('id', sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('batch_id', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_article_failed_imports')),
    )
