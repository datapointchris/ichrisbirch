"""User: set is_admin to not nullable

Revision ID: 372bc2292a38
Revises: b9a4b4ab1d97
Create Date: 2024-05-14 14:33:36.791782

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '372bc2292a38'
down_revision = 'b9a4b4ab1d97'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('UPDATE users SET is_admin = FALSE WHERE is_admin IS NULL')
    op.alter_column('users', 'is_admin', existing_type=sa.BOOLEAN(), nullable=False)


def downgrade() -> None:
    op.alter_column('users', 'is_admin', existing_type=sa.BOOLEAN(), nullable=True)
    op.execute('UPDATE users SET is_admin = NULL WHERE is_admin = FALSE')
