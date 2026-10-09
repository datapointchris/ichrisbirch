"""Each table's check constraints carry the names its model renders.

`alembic check` does not compare check constraints. A constraint renamed in a
migration, or a naming convention changed under the models, passes it unseen
and fails here.
"""

import sqlalchemy as sa

from ichrisbirch.database.base import Base
from ichrisbirch.database.session import get_db_engine
from tests.utils.database import test_settings


def test_every_check_constraint_carries_the_name_its_model_renders():
    mismatched = {}
    with get_db_engine(test_settings).connect() as conn:
        inspector = sa.inspect(conn)
        for fullname, table in sorted(Base.metadata.tables.items()):
            rendered = sorted(c.name for c in table.constraints if isinstance(c, sa.CheckConstraint))
            stored = sorted(c['name'] for c in inspector.get_check_constraints(table.name, schema=table.schema))
            if rendered != stored:
                mismatched[fullname] = {'model': rendered, 'database': stored}
    assert not mismatched, f'check constraint names differ between model and database: {mismatched}'
