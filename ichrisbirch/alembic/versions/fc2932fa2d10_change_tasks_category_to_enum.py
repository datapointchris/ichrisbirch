"""Change tasks category to enum

Revision ID: fc2932fa2d10
Revises: c119daabf840
Create Date: 2023-01-16 02:00:52.070281

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from ichrisbirch.models.tasks import TaskCategory


# revision identifiers, used by Alembic.
revision = 'fc2932fa2d10'
down_revision = 'c119daabf840'
branch_labels = None
depends_on = None


def upgrade() -> None:
    category_enum = postgresql.ENUM(TaskCategory)
    category_enum.create(op.get_bind(), checkfirst=True)
    op.alter_column(
        'tasks',
        'category',
        type_=category_enum,
        postgresql_using='category::taskcategory',
    )


def downgrade() -> None:
    op.alter_column(
        'tasks',
        'category',
        type_=sa.String(length=64),
        postgresql_using='category::varchar',
    )
    category_enum = postgresql.ENUM(TaskCategory)
    category_enum.drop(op.get_bind(), checkfirst=True)
