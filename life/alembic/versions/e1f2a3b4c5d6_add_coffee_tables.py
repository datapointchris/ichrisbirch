"""Add coffee schema with roast_levels, brew_methods, coffee_shops, coffee_beans tables.

Revision ID: e1f2a3b4c5d6
Revises: d4e5f6a7b8c9
Create Date: 2026-04-02
"""

import sqlalchemy as sa
from alembic import op

revision = 'e1f2a3b4c5d6'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE SCHEMA IF NOT EXISTS coffee')

    op.create_table(
        'roast_levels',
        sa.Column('name', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('name'),
        schema='coffee',
    )
    op.execute(
        "INSERT INTO coffee.roast_levels (name) VALUES "
        "('light'), ('medium-light'), ('medium'), ('medium-dark'), ('dark')"
    )

    op.create_table(
        'brew_methods',
        sa.Column('name', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('name'),
        schema='coffee',
    )
    op.execute(
        "INSERT INTO coffee.brew_methods (name) VALUES "
        "('pour-over'), ('espresso'), ('french-press'), ('aeropress'), ('cold-brew'), ('drip'), ('moka-pot')"
    )

    op.create_table(
        'coffee_shops',
        sa.Column('id', sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.Text(), nullable=True),
        sa.Column('state', sa.Text(), nullable=True),
        sa.Column('country', sa.Text(), nullable=True),
        sa.Column('google_maps_url', sa.Text(), nullable=True),
        sa.Column('website', sa.Text(), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('review', sa.Text(), nullable=True),
        sa.Column('date_visited', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='coffee',
    )

    op.create_table(
        'coffee_beans',
        sa.Column('id', sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('roaster', sa.Text(), nullable=True),
        sa.Column('origin', sa.Text(), nullable=True),
        sa.Column('process', sa.Text(), nullable=True),
        sa.Column('roast_level', sa.Text(), nullable=True),
        sa.Column('brew_method', sa.Text(), nullable=True),
        sa.Column('flavor_notes', sa.Text(), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('review', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('purchase_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('coffee_shop_id', sa.Integer(), nullable=True),
        sa.Column('purchase_source', sa.Text(), nullable=True),
        sa.Column('purchase_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['roast_level'], ['coffee.roast_levels.name'], name='fk_coffee_beans_roast_level'),
        sa.ForeignKeyConstraint(['brew_method'], ['coffee.brew_methods.name'], name='fk_coffee_beans_brew_method'),
        sa.ForeignKeyConstraint(
            ['coffee_shop_id'],
            ['coffee.coffee_shops.id'],
            name='fk_coffee_beans_coffee_shop_id',
            ondelete='SET NULL',
        ),
        sa.PrimaryKeyConstraint('id'),
        schema='coffee',
    )


def downgrade() -> None:
    op.drop_table('coffee_beans', schema='coffee')
    op.drop_table('coffee_shops', schema='coffee')
    op.drop_table('brew_methods', schema='coffee')
    op.drop_table('roast_levels', schema='coffee')
    op.execute('DROP SCHEMA IF EXISTS coffee CASCADE')
