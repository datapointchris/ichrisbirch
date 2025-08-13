# Database Troubleshooting

This document covers database-related issues encountered during development, testing, and deployment of the iChrisBirch project.

## Connection Issues

### Database Connection Refused

**Problem:** Application cannot connect to PostgreSQL database.

**Error Messages:**

- `psycopg2.OperationalError: connection to server at "localhost" (127.0.0.1) port 5432 refused`
- `FATAL: database "ichrisbirch" does not exist`
- `FATAL: role "ichrisbirch" does not exist`

**Common Causes and Solutions:**

### 1. Wrong Database Host

```python
# Wrong: Using localhost in containerized environment
DATABASE_URL = "postgresql://user:pass@localhost:5432/db"

# Correct: Using Docker service name
DATABASE_URL = "postgresql://user:pass@postgres:5432/db"
```

### 2. Database Service Not Ready

Add health checks to docker-compose:

```yaml
services:
  postgres:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s

  app:
    depends_on:
      postgres:
        condition: service_healthy
```

### 3. Missing Database or User

```sql
-- Connect as superuser and create database/user
CREATE USER ichrisbirch WITH PASSWORD 'password';
CREATE DATABASE ichrisbirch OWNER ichrisbirch;
GRANT ALL PRIVILEGES ON DATABASE ichrisbirch TO ichrisbirch;
```

### Schema and Table Issues

**Problem:** Tables or schemas don't exist.

**Error Messages:**

- `psycopg2.errors.InvalidSchemaName: schema "ichrisbirch_test" does not exist`
- `sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedTable) relation "users" does not exist`

**Resolution:**

### 1. Run Database Migrations

```bash
# In development
docker-compose exec app uv run alembic upgrade head

# In testing
docker-compose -f docker-compose.test.yml run test-runner uv run alembic upgrade head
```

### 2. Set Schema Environment Variable

```yaml
# docker-compose.test.yml
services:
  test-runner:
    environment:
      - POSTGRES_DB_SCHEMA=ichrisbirch_test
```

### 3. Create Schema Manually

```sql
-- Connect to database and create schema
CREATE SCHEMA IF NOT EXISTS ichrisbirch_test;
ALTER USER ichrisbirch SET search_path TO ichrisbirch_test;
```

## Migration Issues

### Alembic Migration Failures

**Problem:** Database migrations fail to run or create inconsistent state.

**Common Issues:**

#### 1. Migration Revision Conflicts

```bash
# Error: Multiple heads in migration history
FAILED: Multiple head revisions are present for given argument 'head'

# Resolution: Merge migration heads
uv run alembic merge -m "merge migration heads" head_1 head_2
uv run alembic upgrade head
```

#### 2. Missing Migration Dependencies

```bash
# Error: Can't locate revision identified by 'abc123'
# Resolution: Check migration file exists and revision ID is correct
ls ichrisbirch/alembic/versions/
```

#### 3. Manual Schema Changes

```bash
# If manual changes were made, mark as current
uv run alembic stamp head

# Or create new migration from current state
uv run alembic revision --autogenerate -m "sync with manual changes"
```

### Schema Synchronization

**Problem:** Development and test databases have different schemas.

**Resolution:**

```bash
# Reset test database to match development
docker-compose -f docker-compose.test.yml down -v
docker-compose -f docker-compose.test.yml up -d postgres

# Wait for database to be ready
sleep 10

# Run migrations
docker-compose -f docker-compose.test.yml run test-runner uv run alembic upgrade head
```

## Performance Issues

### Slow Query Performance

**Problem:** Database queries are slow, causing application timeouts.

**Diagnosis:**

```sql
-- Enable query logging in PostgreSQL
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 100;  -- Log queries > 100ms
SELECT pg_reload_conf();

-- Check for missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'ichrisbirch_test'
ORDER BY n_distinct DESC;
```

**Resolution:**

#### 1. Add Database Indexes

```sql
-- Create indexes for frequently queried columns
CREATE INDEX CONCURRENTLY idx_habits_user_id ON habits(user_id);
CREATE INDEX CONCURRENTLY idx_habits_created_at ON habits(created_at);
```

#### 2. Optimize SQLAlchemy Queries

```python
# Bad: N+1 query problem
for habit in session.query(Habit).all():
    print(habit.user.username)  # Separate query for each habit

# Good: Use joinedload to eager load relationships
from sqlalchemy.orm import joinedload

habits = session.query(Habit).options(joinedload(Habit.user)).all()
for habit in habits:
    print(habit.user.username)  # No additional queries
```

### Connection Pool Issues

**Problem:** Application runs out of database connections.

**Error Messages:**

- `QueuePool limit of size 20 overflow 10 reached`
- `remaining connection slots are reserved for non-replication superuser connections`

**Resolution:**

#### 1. Configure Connection Pool

```python
# In database configuration
from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    pool_size=10,          # Maximum persistent connections
    max_overflow=20,       # Additional overflow connections
    pool_timeout=30,       # Timeout for getting connection
    pool_recycle=1800,     # Recycle connections every 30 minutes
    pool_pre_ping=True     # Validate connections before use
)
```

#### 2. Ensure Proper Connection Cleanup

```python
# Use context managers for database sessions
from ichrisbirch.database import get_sqlalchemy_session

# Good: Automatic cleanup
def get_user_habits(user_id: int):
    with get_sqlalchemy_session() as session:
        return session.query(Habit).filter(Habit.user_id == user_id).all()
    # Session automatically closed

# Bad: Manual cleanup required
def get_user_habits_bad(user_id: int):
    session = SessionLocal()
    try:
        return session.query(Habit).filter(Habit.user_id == user_id).all()
    finally:
        session.close()  # Easy to forget!
```

## Data Integrity Issues

### Foreign Key Constraint Violations

**Problem:** Data operations fail due to referential integrity constraints.

**Error Messages:**

- `psycopg2.errors.ForeignKeyViolation: insert or update on table "habits" violates foreign key constraint`
- `psycopg2.errors.IntegrityError: duplicate key value violates unique constraint`

**Resolution:**

#### 1. Check Data Dependencies

```sql
-- Verify referenced records exist
SELECT u.id, u.username FROM users u WHERE u.id = 123;

-- Check for constraint violations
SELECT * FROM habits WHERE user_id NOT IN (SELECT id FROM users);
```

#### 2. Handle Dependencies in Code

```python
# Ensure user exists before creating habit
from ichrisbirch.database import get_sqlalchemy_session
from ichrisbirch.models import User, Habit

def create_habit(user_id: int, habit_data: dict):
    with get_sqlalchemy_session() as session:
        # Verify user exists
        user = session.get(User, user_id)
        if not user:
            raise ValueError(f"User {user_id} does not exist")

        # Create habit
        habit = Habit(user_id=user_id, **habit_data)
        session.add(habit)
        session.commit()
        return habit
```

### Data Corruption Issues

**Problem:** Database contains inconsistent or corrupted data.

**Diagnosis:**

```sql
-- Check for data inconsistencies
SELECT
    h.id, h.user_id, u.id as actual_user_id
FROM habits h
LEFT JOIN users u ON h.user_id = u.id
WHERE u.id IS NULL;

-- Verify constraints
SELECT conname, contype FROM pg_constraint WHERE contype = 'f';
```

**Resolution:**

```bash
# Backup database before repairs
docker-compose exec postgres pg_dump -U ichrisbirch ichrisbirch > backup.sql

# Run integrity checks
docker-compose exec postgres psql -U ichrisbirch -d ichrisbirch -c "
VACUUM ANALYZE;
REINDEX DATABASE ichrisbirch;
"
```

## Environment-Specific Issues

### Development vs Production Differences

**Problem:** Database works in development but fails in production.

**Common Causes:**

#### 1. Environment Variable Differences

```bash
# Check environment variables in containers
docker-compose exec app env | grep -i postgres
docker-compose -f docker-compose.prod.yml exec app env | grep -i postgres
```

#### 2. Different PostgreSQL Versions

```yaml
# Pin PostgreSQL version in docker-compose
services:
  postgres:
    image: postgres:15.4  # Specific version instead of 'latest'
```

#### 3. Missing Extensions

```sql
-- Check installed extensions
SELECT * FROM pg_extension;

-- Install required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### SSL Connection Issues

**Problem:** SSL connection errors in production.

**Error Messages:**

- `FATAL: SSL connection is required`
- `SSL error: certificate verify failed`

**Resolution:**

```python
# Update connection string for SSL
DATABASE_URL = "postgresql://user:pass@host:5432/db?sslmode=require"

# For development with self-signed certificates
DATABASE_URL = "postgresql://user:pass@host:5432/db?sslmode=require&sslcert=client.crt&sslkey=client.key&sslrootcert=ca.crt"
```

## Backup and Recovery

### Database Backup Issues

**Problem:** Unable to create or restore database backups.

**Backup Creation:**

```bash
# Create backup with custom format
docker-compose exec postgres pg_dump \
  -U ichrisbirch \
  -d ichrisbirch \
  -f /backup/ichrisbirch_$(date +%Y%m%d_%H%M%S).dump \
  --format=custom \
  --verbose

# Create SQL backup
docker-compose exec postgres pg_dump \
  -U ichrisbirch \
  -d ichrisbirch \
  -f /backup/ichrisbirch_$(date +%Y%m%d_%H%M%S).sql \
  --verbose
```

**Backup Restoration:**

```bash
# Restore from custom format
docker-compose exec postgres pg_restore \
  -U ichrisbirch \
  -d ichrisbirch_restored \
  --clean --create \
  --verbose \
  /backup/ichrisbirch_20231201_120000.dump

# Restore from SQL
docker-compose exec postgres psql \
  -U ichrisbirch \
  -d ichrisbirch_restored \
  -f /backup/ichrisbirch_20231201_120000.sql
```

## Monitoring and Diagnosis

### Database Health Checks

Create a database health check script:

```python
# scripts/db_health_check.py
import sys
from ichrisbirch.config import settings
from ichrisbirch.database import get_sqlalchemy_session
from sqlalchemy import text

def check_database_health():
    """Comprehensive database health check."""
    checks = []

    try:
        with get_sqlalchemy_session() as session:
            # Test basic connectivity
            session.execute(text("SELECT 1"))
            checks.append(("Connection", "OK"))

            # Check table existence
            result = session.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'public'
            """))
            table_count = result.scalar()
            checks.append(("Tables", f"{table_count} tables"))

            # Check recent activity
            result = session.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            checks.append(("Users", f"{user_count} users"))

            # Check for locks
            result = session.execute(text("""
                SELECT COUNT(*) FROM pg_locks
                WHERE NOT granted
            """))
            lock_count = result.scalar()
            checks.append(("Blocked Queries", f"{lock_count} blocked"))

    except Exception as e:
        print(f"Database health check failed: {e}")
        return False

    # Print results
    print("Database Health Check Results:")
    for check, result in checks:
        print(f"  {check}: {result}")

    return True

if __name__ == "__main__":
    if not check_database_health():
        sys.exit(1)
```

### Performance Monitoring

```sql
-- Monitor active connections
SELECT
    state,
    COUNT(*) as connection_count,
    MAX(now() - state_change) as max_duration
FROM pg_stat_activity
WHERE state IS NOT NULL
GROUP BY state;

-- Check slow queries
SELECT
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Monitor database size
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Prevention Checklist

Database management best practices:

- [ ] Use health checks in Docker Compose
- [ ] Pin PostgreSQL version in containers
- [ ] Run migrations in controlled manner
- [ ] Monitor connection pool usage
- [ ] Regular backup validation
- [ ] Set up query performance monitoring
- [ ] Document schema changes
- [ ] Test migrations on copy of production data
- [ ] Use transactions for data modifications
- [ ] Implement proper error handling for database operations
