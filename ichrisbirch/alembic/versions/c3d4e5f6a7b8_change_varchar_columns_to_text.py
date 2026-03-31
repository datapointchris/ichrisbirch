"""Change all varchar and string columns to text

Revision ID: c3d4e5f6a7b8
Revises: 82715aed0fe0
Create Date: 2026-03-31
"""

import sqlalchemy as sa
from alembic import op

revision = 'c3d4e5f6a7b8'
down_revision = '82715aed0fe0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Columns with explicit varchar(N) length limits
    op.alter_column('countdowns', 'name', type_=sa.Text(), existing_type=sa.String(64))
    op.alter_column('articles', 'title', type_=sa.Text(), existing_type=sa.String(256))
    op.alter_column('article_failed_imports', 'batch_id', type_=sa.Text(), existing_type=sa.String(36))
    op.alter_column('personal_api_keys', 'name', type_=sa.Text(), existing_type=sa.String(100))
    op.alter_column('personal_api_keys', 'key_prefix', type_=sa.Text(), existing_type=sa.String(12))
    op.alter_column('autotasks', 'name', type_=sa.Text(), existing_type=sa.String(64))
    op.alter_column('events', 'name', type_=sa.Text(), existing_type=sa.String(256))
    op.alter_column('events', 'venue', type_=sa.Text(), existing_type=sa.String(256))
    op.alter_column('users', 'name', type_=sa.Text(), existing_type=sa.String(100))
    op.alter_column('users', 'password', type_=sa.Text(), existing_type=sa.String(200))
    op.alter_column('money_wasted', 'item', type_=sa.Text(), existing_type=sa.String(64))

    # Columns using bare varchar (no length) - functionally equivalent to text in PostgreSQL
    # but changed for model consistency
    op.alter_column('boxes', 'name', type_=sa.Text(), existing_type=sa.String(), schema='box_packing')
    op.alter_column('items', 'name', type_=sa.Text(), existing_type=sa.String(), schema='box_packing')
    op.alter_column('habits', 'name', type_=sa.Text(), existing_type=sa.String(), schema='habits')
    op.alter_column('categories', 'name', type_=sa.Text(), existing_type=sa.String(), schema='habits')
    op.alter_column('completed', 'name', type_=sa.Text(), existing_type=sa.String(), schema='habits')


def downgrade() -> None:
    op.alter_column('countdowns', 'name', type_=sa.String(64), existing_type=sa.Text())
    op.alter_column('articles', 'title', type_=sa.String(256), existing_type=sa.Text())
    op.alter_column('article_failed_imports', 'batch_id', type_=sa.String(36), existing_type=sa.Text())
    op.alter_column('personal_api_keys', 'name', type_=sa.String(100), existing_type=sa.Text())
    op.alter_column('personal_api_keys', 'key_prefix', type_=sa.String(12), existing_type=sa.Text())
    op.alter_column('autotasks', 'name', type_=sa.String(64), existing_type=sa.Text())
    op.alter_column('events', 'name', type_=sa.String(256), existing_type=sa.Text())
    op.alter_column('events', 'venue', type_=sa.String(256), existing_type=sa.Text())
    op.alter_column('users', 'name', type_=sa.String(100), existing_type=sa.Text())
    op.alter_column('users', 'password', type_=sa.String(200), existing_type=sa.Text())
    op.alter_column('money_wasted', 'item', type_=sa.String(64), existing_type=sa.Text())

    op.alter_column('boxes', 'name', type_=sa.String(), existing_type=sa.Text(), schema='box_packing')
    op.alter_column('items', 'name', type_=sa.String(), existing_type=sa.Text(), schema='box_packing')
    op.alter_column('habits', 'name', type_=sa.String(), existing_type=sa.Text(), schema='habits')
    op.alter_column('categories', 'name', type_=sa.String(), existing_type=sa.Text(), schema='habits')
    op.alter_column('completed', 'name', type_=sa.String(), existing_type=sa.Text(), schema='habits')
