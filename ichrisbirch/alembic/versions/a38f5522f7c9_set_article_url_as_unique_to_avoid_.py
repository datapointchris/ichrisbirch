"""Set article URL as unique to avoid duplicate entries.

Revision ID: a38f5522f7c9
Revises: d34b7e1bd40d
Create Date: 2024-06-09 17:21:31.133708
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = 'a38f5522f7c9'
down_revision = 'd34b7e1bd40d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint('uq_articles_url', 'articles', ['url'])


def downgrade() -> None:
    op.drop_constraint('uq_articles_url', 'articles', type_='unique')
