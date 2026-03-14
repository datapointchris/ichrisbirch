"""convert BoxSize enum to lookup table

Revision ID: d28489933781
Revises: 147500c3d0b3
Create Date: 2026-03-13 23:41:42.199299

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd28489933781'
down_revision = '147500c3d0b3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Create lookup table in box_packing schema
    op.create_table(
        'box_sizes',
        sa.Column('name', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('name', name=op.f('pk_box_sizes')),
        schema='box_packing',
    )

    # Step 2: Insert valid box size values
    op.execute(
        "INSERT INTO box_packing.box_sizes (name) VALUES "
        "('Bag'), ('Book'), ('Large'), ('Medium'), ('Misc'), "
        "('Monitor'), ('Sixteen'), ('Small'), ('UhaulSmall')"
    )

    # Step 3: Convert ENUM column to TEXT
    op.execute("ALTER TABLE box_packing.boxes ALTER COLUMN size TYPE TEXT USING size::text")

    # Step 4: Add FK constraint
    op.create_foreign_key(
        op.f('fk_boxes_size_box_sizes'),
        'boxes', 'box_sizes',
        ['size'], ['name'],
        source_schema='box_packing',
        referent_schema='box_packing',
    )

    # Step 5: Drop the PostgreSQL ENUM type
    op.execute("DROP TYPE boxsize")


def downgrade() -> None:
    op.execute(
        "CREATE TYPE boxsize AS ENUM "
        "('Bag', 'Book', 'Large', 'Medium', 'Misc', 'Monitor', 'Sixteen', 'Small', 'UhaulSmall')"
    )
    op.drop_constraint(op.f('fk_boxes_size_box_sizes'), 'boxes', schema='box_packing', type_='foreignkey')
    op.execute("ALTER TABLE box_packing.boxes ALTER COLUMN size TYPE boxsize USING size::boxsize")
    op.drop_table('box_sizes', schema='box_packing')
