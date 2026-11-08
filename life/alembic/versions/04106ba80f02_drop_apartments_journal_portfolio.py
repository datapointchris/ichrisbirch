"""Drop the apartments, journal and portfolio tables and the apartments schema

`apartments.apartments`, `apartments.features`, `journal` and `portfolio` are
created by the baseline and mapped by no model. Nothing in this repo reads them.

The rows are not carried anywhere, so recovery is a database backup taken
before this ran. The downgrade rebuilds the tables empty, as the baseline built
them.

This runs above the deploy's smoke gate, so a smoke failure leaves the previous
release serving with the tables gone. That release reads none of them.

The schema drop is not CASCADE. An object in `apartments` that the baseline did
not create fails the migration, and the whole upgrade rolls back.

Revision ID: 04106ba80f02
Revises: 21e7c735fce8
Create Date: 2026-10-09 00:26:59.625547

"""

import sqlalchemy as sa
from alembic import op

revision = '04106ba80f02'
down_revision = '21e7c735fce8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table('features', schema='apartments')
    op.drop_table('apartments', schema='apartments')
    op.execute('DROP SCHEMA apartments')
    op.drop_table('journal')
    op.drop_table('portfolio')


def downgrade() -> None:
    op.create_table(
        'portfolio',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('content', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_portfolio')),
    )
    op.create_table(
        'journal',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('content', sa.String(), nullable=True),
        sa.Column('feeling', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_journal')),
    )
    op.execute('CREATE SCHEMA apartments')
    op.create_table(
        'apartments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_apartments')),
        schema='apartments',
    )
    op.create_index(op.f('ix_apartments_apartments_id'), 'apartments', ['id'], unique=False, schema='apartments')
    op.create_index(op.f('ix_apartments_apartments_name'), 'apartments', ['name'], unique=False, schema='apartments')
    op.create_table(
        'features',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('apt_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('value_bool', sa.Boolean(), nullable=True),
        sa.Column('value_str', sa.String(), nullable=True),
        sa.Column('value_int', sa.Integer(), nullable=True),
        sa.Column('value_float', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['apt_id'], ['apartments.apartments.id'], name=op.f('fk_features_apt_id_apartments')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_features')),
        schema='apartments',
    )
    op.create_index(op.f('ix_apartments_features_id'), 'features', ['id'], unique=False, schema='apartments')
