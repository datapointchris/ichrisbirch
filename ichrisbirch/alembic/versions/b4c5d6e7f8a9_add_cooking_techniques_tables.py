"""Add cooking_techniques and cooking_technique_categories tables.

Phase 1 of the Recipes — Cooking Techniques & URL ingestion feature.
Introduces the CookingTechnique entity inside the Recipes domain.
Categories are a lookup table (stable taxonomy of 9), not a Postgres enum.

Revision ID: b4c5d6e7f8a9
Revises: a3b4c5d6e7f8
Create Date: 2026-04-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from ichrisbirch.models.recipe import COOKING_TECHNIQUE_CATEGORIES

revision = 'b4c5d6e7f8a9'
down_revision = 'a3b4c5d6e7f8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'cooking_technique_categories',
        sa.Column('name', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('name', name=op.f('pk_cooking_technique_categories')),
    )

    category_table = sa.table('cooking_technique_categories', sa.column('name', sa.Text()))
    op.bulk_insert(category_table, [{'name': v} for v in COOKING_TECHNIQUE_CATEGORIES])

    op.create_table(
        'cooking_techniques',
        sa.Column('id', sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('slug', sa.Text(), nullable=False),
        sa.Column('category', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('why_it_works', sa.Text(), nullable=True),
        sa.Column('common_pitfalls', sa.Text(), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('source_name', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ['category'],
            ['cooking_technique_categories.name'],
            name=op.f('fk_cooking_techniques_category_cooking_technique_categories'),
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_cooking_techniques')),
        sa.UniqueConstraint('slug', name=op.f('uq_cooking_techniques_slug')),
        sa.CheckConstraint('rating IS NULL OR (rating BETWEEN 1 AND 5)', name=op.f('ck_cooking_techniques_rating_range')),
    )
    op.create_index(op.f('ix_cooking_techniques_category'), 'cooking_techniques', ['category'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_cooking_techniques_category'), table_name='cooking_techniques')
    op.drop_table('cooking_techniques')
    op.drop_table('cooking_technique_categories')
