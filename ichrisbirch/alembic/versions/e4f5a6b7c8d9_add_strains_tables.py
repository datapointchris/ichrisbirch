"""Add strains with its type, status, effect, flavor and terpene vocabularies

A strain is a catalog row in the shape books and coffee beans already have: a
thing tried or waiting to be tried, rated once, and described well enough to
recognize later. Almost every column is nullable, because a label carries
whichever characteristics its producer felt like printing.

Additive and backward-compatible.

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-09-17

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = 'e4f5a6b7c8d9'
down_revision = 'd3e4f5a6b7c8'
branch_labels = None
depends_on = None

# Spelled out rather than imported from ichrisbirch.models.strain. A migration
# is a record of what the database looked like at this revision, and importing
# the constant would rewrite history every time the vocabulary grows.
TYPES = ['cbd', 'hybrid', 'indica', 'indica_dominant', 'ruderalis', 'sativa', 'sativa_dominant']
STATUSES = ['tried', 'want_to_try']
EFFECTS = [
    'creative',
    'energetic',
    'euphoric',
    'focused',
    'giggly',
    'happy',
    'hungry',
    'relaxed',
    'sleepy',
    'talkative',
    'tingly',
    'uplifted',
]
FLAVORS = [
    'berry',
    'cheese',
    'citrus',
    'coffee',
    'diesel',
    'earthy',
    'floral',
    'grape',
    'mint',
    'pine',
    'skunk',
    'spicy',
    'sweet',
    'tropical',
    'vanilla',
    'woody',
]
TERPENES = [
    'bisabolol',
    'caryophyllene',
    'humulene',
    'limonene',
    'linalool',
    'myrcene',
    'nerolidol',
    'ocimene',
    'pinene',
    'terpinolene',
]

LOOKUPS = [
    ('strain_types', TYPES),
    ('strain_statuses', STATUSES),
    ('strain_effects', EFFECTS),
    ('strain_flavors', FLAVORS),
    ('strain_terpenes', TERPENES),
]


def upgrade() -> None:
    for table, values in LOOKUPS:
        created = op.create_table(
            table,
            sa.Column('name', sa.Text(), nullable=False),
            sa.PrimaryKeyConstraint('name', name=op.f(f'pk_{table}')),
        )
        op.bulk_insert(created, [{'name': value} for value in values])

    op.create_table(
        'strains',
        sa.Column('id', sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('breeder', sa.Text(), nullable=True),
        sa.Column('lineage', sa.Text(), nullable=True),
        sa.Column('strain_type', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), server_default='want_to_try', nullable=False),
        sa.Column('thc_percent', sa.Float(), nullable=True),
        sa.Column('cbd_percent', sa.Float(), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('effects', postgresql.ARRAY(sa.Text()), server_default='{}', nullable=False),
        sa.Column('flavors', postgresql.ARRAY(sa.Text()), server_default='{}', nullable=False),
        sa.Column('terpenes', postgresql.ARRAY(sa.Text()), server_default='{}', nullable=False),
        sa.Column('tags', postgresql.ARRAY(sa.Text()), server_default='{}', nullable=False),
        sa.Column('source', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('review', sa.Text(), nullable=True),
        sa.Column('last_tried_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('rating IS NULL OR (rating BETWEEN 1 AND 10)', name='rating_range'),
        # NULLS NOT DISTINCT so two rows named the same with no breeder collide.
        # Postgres treats nulls as distinct by default, which would let the
        # unknown-breeder case duplicate freely — and that is the common case.
        sa.UniqueConstraint('name', 'breeder', name=op.f('uq_strains_name'), postgresql_nulls_not_distinct=True),
        sa.ForeignKeyConstraint(['strain_type'], ['strain_types.name'], name=op.f('fk_strains_strain_type_strain_types')),
        sa.ForeignKeyConstraint(['status'], ['strain_statuses.name'], name=op.f('fk_strains_status_strain_statuses')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_strains')),
    )
    op.create_index('ix_strains_strain_type', 'strains', ['strain_type'])
    op.create_index('ix_strains_status', 'strains', ['status'])


def downgrade() -> None:
    op.drop_index('ix_strains_status', table_name='strains')
    op.drop_index('ix_strains_strain_type', table_name='strains')
    op.drop_table('strains')
    for table, _ in reversed(LOOKUPS):
        op.drop_table(table)
