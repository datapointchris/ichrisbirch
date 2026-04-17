"""Add recipes and recipe_ingredients tables plus lookup tables.

Revision ID: a3b4c5d6e7f8
Revises: f2a3b4c5d6e7
Create Date: 2026-04-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from ichrisbirch.models.recipe import RECIPE_CUISINES
from ichrisbirch.models.recipe import RECIPE_DIFFICULTIES
from ichrisbirch.models.recipe import RECIPE_MEAL_TYPES
from ichrisbirch.models.recipe import RECIPE_UNITS

revision = 'a3b4c5d6e7f8'
down_revision = 'f2a3b4c5d6e7'
branch_labels = None
depends_on = None


def _seed_lookup(table_name: str, values: list[str]) -> None:
    table = sa.table(table_name, sa.column('name', sa.Text()))
    op.bulk_insert(table, [{'name': v} for v in values])


def upgrade() -> None:
    op.create_table(
        'recipe_units',
        sa.Column('name', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('name', name=op.f('pk_recipe_units')),
    )
    op.create_table(
        'recipe_difficulty',
        sa.Column('name', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('name', name=op.f('pk_recipe_difficulty')),
    )
    op.create_table(
        'recipe_cuisine',
        sa.Column('name', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('name', name=op.f('pk_recipe_cuisine')),
    )
    op.create_table(
        'recipe_meal_type',
        sa.Column('name', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('name', name=op.f('pk_recipe_meal_type')),
    )

    _seed_lookup('recipe_units', RECIPE_UNITS)
    _seed_lookup('recipe_difficulty', RECIPE_DIFFICULTIES)
    _seed_lookup('recipe_cuisine', RECIPE_CUISINES)
    _seed_lookup('recipe_meal_type', RECIPE_MEAL_TYPES)

    op.create_table(
        'recipes',
        sa.Column('id', sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('source_name', sa.Text(), nullable=True),
        sa.Column('prep_time_minutes', sa.Integer(), nullable=True),
        sa.Column('cook_time_minutes', sa.Integer(), nullable=True),
        sa.Column('total_time_minutes', sa.Integer(), nullable=True),
        sa.Column('servings', sa.Integer(), server_default='4', nullable=False),
        sa.Column('difficulty', sa.Text(), nullable=True),
        sa.Column('cuisine', sa.Text(), nullable=True),
        sa.Column('meal_type', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('instructions', sa.Text(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('times_made', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_made_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['difficulty'], ['recipe_difficulty.name'], name=op.f('fk_recipes_difficulty_recipe_difficulty')),
        sa.ForeignKeyConstraint(['cuisine'], ['recipe_cuisine.name'], name=op.f('fk_recipes_cuisine_recipe_cuisine')),
        sa.ForeignKeyConstraint(['meal_type'], ['recipe_meal_type.name'], name=op.f('fk_recipes_meal_type_recipe_meal_type')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_recipes')),
        sa.UniqueConstraint('source_url', name=op.f('uq_recipes_source_url')),
    )

    op.create_table(
        'recipe_ingredients',
        sa.Column('id', sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column('recipe_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=True),
        sa.Column('unit', sa.Text(), nullable=True),
        sa.Column('item', sa.Text(), nullable=False),
        sa.Column('prep_note', sa.Text(), nullable=True),
        sa.Column('is_optional', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('ingredient_group', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ['recipe_id'], ['recipes.id'], ondelete='CASCADE', name=op.f('fk_recipe_ingredients_recipe_id_recipes')
        ),
        sa.ForeignKeyConstraint(
            ['unit'], ['recipe_units.name'], name=op.f('fk_recipe_ingredients_unit_recipe_units')
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_recipe_ingredients')),
    )
    op.create_index(
        op.f('ix_recipe_ingredients_recipe_id'),
        'recipe_ingredients',
        ['recipe_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_recipe_ingredients_item'),
        'recipe_ingredients',
        ['item'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_recipe_ingredients_item'), table_name='recipe_ingredients')
    op.drop_index(op.f('ix_recipe_ingredients_recipe_id'), table_name='recipe_ingredients')
    op.drop_table('recipe_ingredients')
    op.drop_table('recipes')
    op.drop_table('recipe_meal_type')
    op.drop_table('recipe_cuisine')
    op.drop_table('recipe_difficulty')
    op.drop_table('recipe_units')
