"""User: alternative_id int -> bigint, add is_admin column

Revision ID: b9a4b4ab1d97
Revises: d2922c54fe22
Create Date: 2024-05-14 14:25:55.732666

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b9a4b4ab1d97'
down_revision = 'd2922c54fe22'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=True, default=False))
    op.alter_column('users', 'last_login', existing_type=postgresql.TIMESTAMP(timezone=True), nullable=False)
    op.alter_column('users', 'alternative_id', type=sa.BIGINT)


def downgrade() -> None:
    op.alter_column('users', 'last_login', existing_type=postgresql.TIMESTAMP(timezone=True), nullable=True)
    op.alter_column('users', 'alternative_id', type=sa.INTEGER)
    op.drop_column('users', 'is_admin')
