# Alembic Migrations

Run from `ichrisbirch/ichrisbirch` (where `alembic.ini` is located).

## Creating a Migration

```bash
# 1. Make changes to models/schemas
# 2. Generate migration
alembic revision --autogenerate -m 'add notes field to tasks table'
# 3. Review the generated file — autogenerate is not perfect
# 4. Apply locally
alembic upgrade head
```

For data migrations (INSERT, UPDATE, type conversions), use `alembic revision -m '...'` without `--autogenerate` and write the migration by hand.

## Squashing Migrations

When migration history gets too long or messy, squash into a single baseline.

**The key rule: set the new baseline's `revision` ID to match the current production head.** This way production's `alembic_version` already matches and `alembic upgrade head` is a no-op. No stamping, no deploy failures.

### Procedure

```bash
# 1. Check what revision production is on
ssh chris@10.0.20.11 "docker exec icb-prod-api python -c \"
from sqlalchemy import text
from ichrisbirch.config import get_settings
from ichrisbirch.database.session import get_db_engine
engine = get_db_engine(get_settings())
with engine.connect() as c:
    print(c.execute(text('SELECT version_num FROM alembic_version')).scalar())
\""
# Example output: e010f859f025

# 2. Delete all migration files
rm ichrisbirch/alembic/versions/*.py

# 3. Drop test database and recreate schemas
#    drop_all_tables now issues `DROP SCHEMA ... CASCADE` for every non-system
#    schema via live introspection, then create_schemas recreates the configured set.
ENVIRONMENT=testing POSTGRES_HOST=localhost POSTGRES_PORT=5434 \
  python -c "
from ichrisbirch.config import get_settings
from ichrisbirch.database.initialization import drop_all_tables, create_schemas
from ichrisbirch.database.session import create_session
settings = get_settings()
drop_all_tables(settings)
with create_session(settings) as session:
    create_schemas(session, settings)
"

# 4. Generate new baseline
cd ichrisbirch
ENVIRONMENT=testing POSTGRES_HOST=localhost POSTGRES_PORT=5434 \
  alembic revision --autogenerate -m "baseline schema"

# 5. CRITICAL: Change the revision ID to match production's current head
# In the generated file, change:
#   revision = 'abc123random'
# To:
#   revision = 'e010f859f025'  # whatever production is on
# Also rename the file to match.

# 6. Add INSERT statements for lookup table data
# Autogenerate only handles DDL (CREATE TABLE), not DML (INSERT).
# Lookup tables need their rows inserted in the migration.

# 7. Verify from clean database
alembic upgrade head
alembic check  # should say "No new upgrade operations detected"

# 8. Run full test suite, then deploy
```

### Why this works

Production's `alembic_version` table contains `e010f859f025`. The new baseline migration also has `revision = 'e010f859f025'`. When `alembic upgrade head` runs, it sees the database is already at head — nothing to do. New databases (dev/test) run the single migration from scratch.

### Common mistakes

- **Using a new random revision ID**: Production can't find its current revision in the new chain → deploy fails with "Can't locate revision"
- **Deleting migrations before stamping production**: Same failure — production references a revision that no longer exists
- **Forgetting INSERT statements**: Autogenerate only creates tables, not data. Lookup tables need their rows inserted in the migration
- **Using `alembic stamp --purge` as a deployment strategy**: This is a recovery tool, not a workflow. If you need `--purge`, something already went wrong

## Lookup Tables (Replacing PostgreSQL ENUMs)

Never use PostgreSQL ENUM types. Use lookup tables with text primary keys instead. See the [enum removal memory](../CLAUDE.md) for rationale.

### Adding a new value to an existing lookup table

```bash
# 1. Add to the constant list in the model file (e.g. TASK_CATEGORIES in task.py)
# 2. Create a migration:
alembic revision -m "add Gaming task category"
# 3. Write the migration by hand:
#    op.execute("INSERT INTO task_categories (name) VALUES ('Gaming')")
# 4. Deploy normally — alembic runs the migration
```

### Creating a new lookup table for a new feature

```python
# Model (in ichrisbirch/models/)
class MyLookup(Base):
    __tablename__ = 'my_lookups'
    name: Mapped[str] = mapped_column(Text, primary_key=True)

# Column that references it
category: Mapped[str] = mapped_column(Text, ForeignKey('my_lookups.name'), nullable=False)

# Schema (in ichrisbirch/schemas/) — just use str, not an enum
category: str
```

## Key Commands

| Command | What it does |
| ------- | ------------ |
| `alembic revision --autogenerate -m "msg"` | Generate migration from model changes |
| `alembic revision -m "msg"` | Create empty migration (for hand-written) |
| `alembic upgrade head` | Apply all pending migrations |
| `alembic downgrade -1` | Roll back one migration |
| `alembic current` | Show current database revision |
| `alembic history` | Show migration chain |
| `alembic check` | Verify models match database (no pending changes) |
| `alembic stamp <rev>` | Set alembic_version without running migrations |
| `alembic stamp --purge <rev>` | Force-set alembic_version (recovery only) |

## Troubleshooting

**"Can't locate revision"**: Production's `alembic_version` points to a revision that doesn't exist in the current migration files. Usually means migrations were squashed without matching the revision ID. Fix with `alembic stamp --purge head`, but understand why it happened first.

**"Target database is not up to date"**: Run `alembic upgrade head`. If that fails, check `SELECT version_num FROM alembic_version` and compare against `alembic history`.

**Tests vs production use different code paths**: Tests now use `alembic upgrade head` (same as production). If a migration has a bug, tests will catch it. If tests use `create_all` instead, migration bugs are invisible until production deploy.
