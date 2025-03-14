"""autotasks: manual remove all autotask tasks above max_concurrency

Revision ID: bb9555ffa490
Revises: e8cc676580bc
Create Date: 2025-03-14 05:11:56.655615

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = 'bb9555ffa490'
down_revision = 'e8cc676580bc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        with ordered as
            (
            select
                tasks.*,
                rank() over(partition by tasks.name order by tasks.add_date) as name_rank
            from tasks
            join autotasks on autotasks.name = tasks.name
            )
        delete from tasks
        where id in (select id from ordered where name_rank not in (1, 2));
               """
    )


def downgrade() -> None:
    # YOU ARE FUCKED
    pass
