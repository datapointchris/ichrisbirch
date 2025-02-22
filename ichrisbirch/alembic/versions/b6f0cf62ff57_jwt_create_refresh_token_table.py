"""jwt: create refresh token table

Revision ID: b6f0cf62ff57
Revises: 0355fe5a7fc8
Create Date: 2025-02-22 00:55:01.300880

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'b6f0cf62ff57'
down_revision = '0355fe5a7fc8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'jwt_refresh_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Text(), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=False),
        sa.Column('date_stored', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_jwt_refresh_tokens')),
    )


def downgrade() -> None:
    op.drop_table('jwt_refresh_tokens')
