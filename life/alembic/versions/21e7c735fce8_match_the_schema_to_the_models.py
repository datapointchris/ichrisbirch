"""Match the schema to the models where the migrations built it differently

`articles.tags` becomes `text[]`, the type its model and every other tags
column carry. `varchar` has no operators of its own and casts to `text` without
conversion, so the release serving while this runs compares and reads the same
rows before and after.

`ix_recipe_ingredients_item` is dropped. Its only reader matches the column
with `ILIKE '%term%'`, which a btree index cannot serve.

The `job_run_id` index takes the name the naming convention gives a column in
the `admin` schema, as `ix_admin_scheduler_job_runs_job_id` already does. No
code names an index.

Revision ID: 21e7c735fce8
Revises: 464a363261aa
Create Date: 2026-10-09 00:17:49.202366

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = '21e7c735fce8'
down_revision = '464a363261aa'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        'articles',
        'tags',
        type_=postgresql.ARRAY(sa.Text()),
        existing_type=postgresql.ARRAY(sa.String()),
        existing_nullable=True,
    )
    op.drop_index(op.f('ix_recipe_ingredients_item'), table_name='recipe_ingredients')
    op.execute('ALTER INDEX admin.ix_scheduler_job_runs_job_run_id RENAME TO ix_admin_scheduler_job_runs_job_run_id')


def downgrade() -> None:
    op.execute('ALTER INDEX admin.ix_admin_scheduler_job_runs_job_run_id RENAME TO ix_scheduler_job_runs_job_run_id')
    op.create_index(op.f('ix_recipe_ingredients_item'), 'recipe_ingredients', ['item'], unique=False)
    op.alter_column(
        'articles',
        'tags',
        type_=postgresql.ARRAY(sa.String()),
        existing_type=postgresql.ARRAY(sa.Text()),
        existing_nullable=True,
    )
