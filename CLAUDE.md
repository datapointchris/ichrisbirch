# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

iChrisBirch is a personal productivity web application with a **multi-service architecture**: FastAPI backend (API), Flask frontend (App), Streamlit chat interface, and APScheduler service. All services share a PostgreSQL database and Redis cache, orchestrated via Docker Compose with Traefik reverse proxy.

**Key Technologies**: Python 3.13, FastAPI, Flask, Streamlit, SQLAlchemy 2.0, PostgreSQL 16, Redis, Traefik v3.4

**Package Management**: uv (locked dependencies in `uv.lock`)

## Essential Commands

### Development Environment

Start development with HTTPS and Traefik (one command does it all):

```bash
./cli/ichrisbirch dev start       # Start all services with HTTPS
./cli/ichrisbirch dev status      # Show container status + URLs
./cli/ichrisbirch dev health      # Comprehensive health checks
./cli/ichrisbirch dev logs        # Live Docker logs (colored)
./cli/ichrisbirch dev stop        # Stop all services
./cli/ichrisbirch dev restart     # Restart services
./cli/ichrisbirch dev rebuild     # Rebuild images and restart
```

Access at:

- API: <https://api.docker.localhost/>
- App: <https://app.docker.localhost/>
- Chat: <https://chat.docker.localhost/>
- Dashboard: <https://dashboard.docker.localhost/> (dev/devpass)

### Testing Environment

Tests reuse containers for fast iteration (database reset ensures clean state):

```bash
./cli/ichrisbirch test run              # Reuses containers, resets database
./cli/ichrisbirch test run -v           # With verbose output
./cli/ichrisbirch test cov              # Run with coverage
```

Containers stay running after tests for quick re-runs:

```bash
./cli/ichrisbirch testing start         # Start containers manually
./cli/ichrisbirch testing stop          # Stop containers (clears volumes)
./cli/ichrisbirch testing health        # Health checks
./cli/ichrisbirch testing logs          # View logs (auto-reconnect)
```

Access at: <https://api.test.localhost:8443/>

### Production Environment

**Production runs on the homelab, NOT locally.**

- **Production server**: `ssh chris@10.0.20.11`
- **Application path**: `/srv/ichrisbirch/`
- **Webhook server**: `ssh chris@10.0.20.15`
- **Webhook code**: Lives locally at `~/homelab`

### Database Operations

```bash
# Migrations (Alembic)
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1

# Initialize database (for any environment)
python -m ichrisbirch.database.initialization --env development|testing|production
```

### Testing

```bash
# Run all tests (reuses containers, resets database)
./cli/ichrisbirch test run

# Run specific test file
./cli/ichrisbirch test run tests/ichrisbirch/api/test_tasks.py

# Run with coverage
./cli/ichrisbirch test cov

# Run specific test with verbose output
./cli/ichrisbirch test run tests/ichrisbirch/api/test_tasks.py::test_create_task -v

# Stop containers when done (optional - they persist for fast re-runs)
./cli/ichrisbirch testing stop
```

### Code Quality

```bash
# Linting and formatting
uv run ruff check .
uv run ruff format .

# Type checking
uv run mypy ichrisbirch/

# Pre-commit hooks
pre-commit run --all-files
```

### Documentation Commands

```bash
# Serve docs locally
mkdocs serve

# Build docs
mkdocs build
```

## Architecture

### Multi-Service Design

**API Service** (`ichrisbirch/api/`)

- **Framework**: FastAPI 0.111.0+
- **Port**: 8000 (dev), 8001 (test)
- **Entry Point**: `ichrisbirch.wsgi_api:api`
- **Purpose**: RESTful backend API with JWT authentication
- **Endpoints**: `/auth`, `/users`, `/tasks`, `/habits`, `/events`, `/books`, `/articles`, `/chat/*`, etc.

**App Service** (`ichrisbirch/app/`)

- **Framework**: Flask 3.0.3+
- **Port**: 5000 (dev), 5001 (test)
- **Entry Point**: `ichrisbirch.wsgi_app:app`
- **Purpose**: Server-side rendered frontend with Flask-Login sessions
- **Routes**: Blueprints for auth, admin, tasks, habits, events, chat, etc.

**Chat Service** (`ichrisbirch/chat/`)

- **Framework**: Streamlit 1.41.1+
- **Port**: 8505 (dev), 8507 (test)
- **Entry Point**: `ichrisbirch/chat/app.py`
- **Purpose**: AI-powered chat interface with OpenAI integration
- **Features**: JWT authentication via cookies, persistent chat history

**Scheduler Service** (`ichrisbirch/scheduler/`)

- **Framework**: APScheduler 3.10.4+ (BlockingScheduler)
- **Entry Point**: `ichrisbirch.wsgi_scheduler`
- **Jobs**: Daily task priority decrease (1 AM), AutoTask creation (1:15 AM), PostgreSQL backup to S3 (1:30 AM)
- **Job Store**: SQLAlchemy-backed (Postgres) for persistence

**Infrastructure Services**:

- PostgreSQL 16 (port 5432 dev, 5434 test)
- Redis 7 (port 6379 dev, 6380 test)
- Traefik v3.4 reverse proxy (HTTPS, WebSocket support, rate limiting)

### Database Patterns

**ORM**: SQLAlchemy 2.0 with declarative base (`ichrisbirch/database/base.py`)

**Session Management**:

```python
# Context manager pattern
from ichrisbirch.database.session import create_session

with create_session(settings) as session:
    # Database operations
    session.commit()
```

**FastAPI Dependency Injection**:

```python
from ichrisbirch.api.dependencies import get_sqlalchemy_session

@router.get('/')
async def read_all(session: Session = Depends(get_sqlalchemy_session)):
    # session is automatically provided
```

**Models** (`ichrisbirch/models/`): User, Task, Habit, Event, Book, Article, Chat, ChatMessage, AutoTask, Box, BoxItem, etc.

**Migrations**: Alembic (`ichrisbirch/alembic/`)

- All models imported in `alembic/env.py` for autogenerate
- Run migrations before tests if schema changes

### Schema Validation

**Pydantic Schemas** (`ichrisbirch/schemas/`):

- `*Create` schemas: POST request validation
- Base schemas: GET response serialization
- `*Update` schemas: PATCH partial updates (all fields optional)
- `ConfigDict(from_attributes=True)`: Convert SQLAlchemy models to Pydantic

### Configuration System

**Centralized Config**: `ichrisbirch/config.py`

**Settings Structure**:

```python
class Settings:
    ai: AISettings
    auth: AuthSettings
    aws: AWSSettings
    postgres: PostgresSettings
    sqlalchemy: SQLAlchemySettings
    # ... 12 nested settings classes
```

**Environment Loading**:

- Development/Testing: `.env` file
- Production: AWS Systems Manager Parameter Store
- Set `ENVIRONMENT=development|testing|production`

**Database URI Format**: `postgresql+psycopg://{user}:{pass}@{host}:{port}/{db}`

### Authentication Flow

**Flask (App Service)**:

- Flask-Login for session management
- CSRF protection via Flask-WTF
- Session cookies for state

**FastAPI (API Service)**:

- JWT tokens (access + refresh)
- `Authorization: Bearer {token}` header
- Refresh tokens stored in database
- Access token expiration: 15 minutes
- Refresh token expiration: 7 days

**Streamlit (Chat Service)**:

- JWT tokens stored in cookies
- Automatic refresh on expiration
- Session-based authentication state

**Protected Routes**:

```python
# FastAPI
from ichrisbirch.api.dependencies import auth

@router.get('/')
async def protected(user: User = Depends(auth.get_current_user)):
    # user is authenticated

# Admin-only
@router.post('/admin-only')
async def admin(user: User = Depends(auth.get_current_admin_user)):
    # user is authenticated and admin
```

## Testing Architecture

### Test Environment

**Containerized Testing**: Separate Docker Compose environment

- Isolated test database (port 5434)
- Isolated test Redis (port 6380)
- Services on alternate ports (run alongside dev)
- Automatic initialization via `ichrisbirch.database.initialization` module

### Test Fixtures

**Location**: `tests/conftest.py`

**Session-Scoped** (run once):

- `setup_test_environment`: Docker Compose orchestration
- `create_drop_tables`: Table lifecycle management
- `insert_users_for_login`: Test users (admin + regular)

**Module-Scoped** (per test file):

- `test_api`: Unauthenticated API client
- `test_api_logged_in`: Authenticated regular user
- `test_api_logged_in_admin`: Authenticated admin user
- `test_app`: Flask app client
- `test_app_logged_in`: Flask app with session

**Function-Scoped** (per test):

- Same fixtures with `_function` suffix for isolation

### Test Data

**Location**: `tests/test_data/`

- Structured test data for each model
- Faker-based data generation
- Reusable across test modules

**Coverage**: 77+ test files covering API endpoints, app routes, models, schemas, authentication, scheduler jobs

## Deployment

### Multi-Stage Docker Build

**Dockerfile Stages**:

- `base`: Python 3.13 base with uv
- `development-builder`: Build with all dependencies
- `development`: Dev runtime with hot reload
- `testing`: Production runtime + test dependencies
- `production-builder`: Build production dependencies only
- `production`: Minimal runtime (non-root user, no dev deps)

**Build Targets**: Specify `--target development|testing|production`

### Docker Compose Environments

**Development** (`docker-compose.dev.yml`):

- Hot reload for all services
- Source code mounted as volume
- HTTPS via Traefik (*.docker.localhost)
- Traefik dashboard accessible
- Full dev dependencies

**Testing** (`docker-compose.test.yml`):

- Runs simultaneously with dev (different ports)
- Isolated database and Redis
- Production-like behavior (no hot reload)
- Test-specific configurations

**Production** (`docker-compose.yml`):

- Optimized images (multi-stage build)
- Non-root user for security
- No external port exposure (all through Traefik)
- Resource limits and health checks
- AWS credentials mounted as read-only volume

### Critical: Dev/Test vs Production Builds

**Dev and Test environments use bind mounts** - the code comes from the local filesystem, not the Docker image. This means Docker build issues may NOT be caught in dev/test.

| Environment | Code Source | Tests Docker Build? |
|-------------|-------------|---------------------|
| Development | Bind mount `.:/app` | NO |
| Testing | Bind mount `.:/app` | NO |
| CI | Bind mount `.:/app` | NO (but CI has separate prod build test) |
| **Production** | `COPY . /app` in Dockerfile | **YES** |

**Always test production builds before deploying Docker/Compose changes:**

```bash
# Test that production build works
icb prod build-test

# This runs: docker compose -f docker-compose.yml build
# If it fails, the same failure will happen in production
```

The CI pipeline includes a `test-production-build` job that catches these issues automatically.

### Traefik Configuration

**Dynamic Config**: `deploy-containers/traefik/dynamic/`

- Middleware: CORS, security headers, rate limiting
- TLS configuration
- Environment-specific overrides

**SSL Certificates**: `deploy-containers/traefik/certs/`

- Development: mkcert browser-trusted certificates
- Production: Let's Encrypt (planned)

**Management**:

```bash
./cli/ichrisbirch ssl-manager generate dev
./cli/ichrisbirch ssl-manager validate all
./cli/ichrisbirch ssl-manager info prod
```

## Development Patterns

### Adding a New Feature

1. **Create Model** (`ichrisbirch/models/`)
   - Inherit from `Base`
   - Use `Mapped[type]` for type hints
   - Define relationships with `relationship()`

2. **Create Schema** (`ichrisbirch/schemas/`)
   - `*Create` schema for POST
   - Base schema for GET (include all fields)
   - `*Update` schema for PATCH (all fields optional)
   - Set `ConfigDict(from_attributes=True)`

3. **Create API Endpoint** (`ichrisbirch/api/endpoints/`)
   - Use FastAPI router
   - Dependency inject `Session` and `User`
   - Return Pydantic schemas

4. **Create Flask Route** (`ichrisbirch/app/routes/`)
   - Create blueprint
   - Use Flask-Login for auth
   - Communicate with API via `logging_flask_session_client()` or `logging_internal_service_client()` from `ichrisbirch.api.client.logging_client`

5. **Create Templates** (`ichrisbirch/app/templates/`)
   - Jinja2 templates
   - Extend base template
   - Use WTForms for forms (CSRF protection)

6. **Write Tests** (`tests/ichrisbirch/`)
   - Mirror source structure
   - Test API endpoints (CRUD)
   - Test app routes (rendering)
   - Use fixtures for authenticated clients

7. **Create Migration**

   ```bash
   alembic revision --autogenerate -m "add feature"
   alembic upgrade head
   ```

### Factory Pattern for App Creation

Both FastAPI and Flask use factory functions:

```python
# ichrisbirch/api/main.py
def create_api(settings: Settings) -> FastAPI:
    api = FastAPI(...)
    # Configure middleware, routes, etc.
    return api

# ichrisbirch/app/main.py
def create_app(settings: Settings) -> Flask:
    app = Flask(__name__)
    # Configure blueprints, middleware, etc.
    return app
```

### Blueprint Pattern (Flask)

Each feature organized as a blueprint:

```python
# ichrisbirch/app/routes/tasks.py
from flask import Blueprint, render_template

blueprint = Blueprint('tasks', __name__, url_prefix='/tasks')

@blueprint.route('/')
def index():
    # Route implementation
    return render_template('tasks/index.html')
```

Register in `main.py`:

```python
from ichrisbirch.app.routes import tasks
app.register_blueprint(tasks.blueprint)
```

### Dependency Injection (FastAPI)

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from ichrisbirch.api.dependencies import get_sqlalchemy_session, auth
from ichrisbirch.models import User

@router.post('/', response_model=schemas.Task)
async def create(
    task: schemas.TaskCreate,
    session: Session = Depends(get_sqlalchemy_session),
    user: User = Depends(auth.get_current_user)
):
    # session and user automatically injected
    new_task = Task(**task.model_dump(), user_id=user.id)
    session.add(new_task)
    session.commit()
    return new_task
```

## Important Notes

### Virtual Environment

Always check for and use the virtual environment:

```bash
# Activate venv if not active
source .venv/bin/activate

# Run commands via uv
uv run pytest
uv run python script.py
```

### Python Version

Use `python`, not `python3` (as per project standards).

### Naming Conventions

- **Documentation files**: Use lowercase (e.g., `quick-start.md`, not `Quick-Start.md`)
- **Docker containers**: Prefixed with `icb-{env}-{service}` (e.g., `icb-dev-api`)
- **Database naming**: Snake_case for tables and columns

### Error Handling

Always fix errors when encountered - never skip them to move faster. Document critical errors if they cannot be fixed immediately.

### Emoji Usage

Use emojis sparingly:

- ✅ Green checkmark for pass
- ❌ Red X for fail
- Other visual indicators where appropriate
- Avoid smiling faces or silly emojis

### Logging Strategy

The project uses **structlog** with stdout-only output. All logs go to stdout, Docker handles persistence.

**Logger pattern** (every module):

```python
import structlog
logger = structlog.get_logger()

# Log with structured data
logger.info('user_login_success', user_id=user.id, email=user.email)
```

**Configuration** (environment variables):

- `LOG_FORMAT`: `console` (default) or `json`
- `LOG_LEVEL`: `DEBUG` (default), `INFO`, `WARNING`, `ERROR`
- `LOG_COLORS`: `auto` (default), `true`, `false`

**Viewing logs** (CLI commands with auto-reconnect):

```bash
./cli/ichrisbirch dev logs       # All services, colored
./cli/ichrisbirch dev logs api   # Specific service
./cli/ichrisbirch testing logs   # Test environment
```

**Request tracing**: All services include `request_id` in logs via `X-Request-ID` header propagation.

### Production Deployment Logs

When production deployments fail, logs are in multiple locations:

| Log Type | Location | Command |
|----------|----------|---------|
| Deployment events | `/srv/ichrisbirch/logs/deploy.log` | `icb prod logs deploy` |
| Build output | `/srv/ichrisbirch/logs/build-*.log` | `icb prod logs build` |
| Container logs | Docker | `icb prod logs` or `docker logs icb-prod-<service>` |
| Webhook execution | `/opt/webhooks/logs/` on 10.0.20.15 | SSH to webhook server |

**Troubleshooting deployment failures:**

```bash
# SSH to production server
ssh chris@10.0.20.11

# Check deployment log
icb prod logs deploy

# Check build output (if rebuild failed)
icb prod logs build

# Check container logs
icb prod logs api
docker logs icb-prod-api --tail=100
```

**If containers don't exist** (never started), check the webhook server:

```bash
ssh chris@10.0.20.15
ls -lt /opt/webhooks/logs/ichrisbirch-*.log | head -5
tail -200 /opt/webhooks/logs/ichrisbirch-<latest>.log
```

### Pre-commit Hooks

Project uses pre-commit for code quality:

- Ruff formatting and linting
- djlint for Jinja templates
- mypy type checking
- Runs automatically on commit

Bypass only when absolutely necessary:

```bash
git commit --no-verify -m "message"
```

### Python Imports and Paths

**NEVER modify `sys.path`**. If you find yourself needing to modify `sys.path`, you're doing something wrong. The codebase is structured as a proper Python package - use standard imports.

**NEVER use multiple `.parent` calls** like `Path(__file__).parent.parent.parent`. This is fragile and breaks when files move. Instead, use the `find_project_root()` function from `ichrisbirch.util`:

```python
# WRONG - fragile, breaks when files move
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# CORRECT - use find_project_root
from ichrisbirch.util import find_project_root
project_root = find_project_root()
```

**Scripts and tools** should either:

1. Be run as modules: `python -m tools.my_script`
2. Use proper package imports without path manipulation
3. Use `find_project_root()` if they need the project root path

**NEVER use `# noqa` comments** to bypass linting errors for import order (E402). If imports must be after code, restructure the code instead.

## Common Workflows

### Daily Development

```bash
# Start development environment
./cli/ichrisbirch dev start

# Make changes, tests run automatically via hot reload

# Check logs if needed
./cli/ichrisbirch dev logs api

# Stop when done
./cli/ichrisbirch dev stop
```

### Testing Workflow

```bash
# Run all tests (reuses containers, resets database each run)
./cli/ichrisbirch test run

# Run specific test
./cli/ichrisbirch test run tests/ichrisbirch/api/test_tasks.py -v

# Run with coverage
./cli/ichrisbirch test cov

# View coverage report
open htmlcov/index.html

# View test logs while debugging
./cli/ichrisbirch testing logs api

# Stop containers when done (they persist for fast re-runs)
./cli/ichrisbirch testing stop
```

### Database Migration Workflow

```bash
# Make model changes in ichrisbirch/models/

# Generate migration
alembic revision --autogenerate -m "add column to tasks"

# Review migration in ichrisbirch/alembic/versions/

# Apply migration
alembic upgrade head

# If needed, rollback
alembic downgrade -1
```

### Adding API Endpoint

```bash
# 1. Create/modify model (ichrisbirch/models/)
# 2. Create/modify schema (ichrisbirch/schemas/)
# 3. Create endpoint (ichrisbirch/api/endpoints/)
# 4. Write tests (tests/ichrisbirch/api/)
# 5. Run tests
uv run pytest tests/ichrisbirch/api/test_new_feature.py -v

# 6. If schema changed, create migration
alembic revision --autogenerate -m "add new feature"
alembic upgrade head
```

## Project Structure Summary

```text
ichrisbirch/
├── ichrisbirch/              # Main application code
│   ├── api/                  # FastAPI backend
│   │   ├── endpoints/        # API route definitions
│   │   └── main.py          # FastAPI factory
│   ├── app/                  # Flask frontend
│   │   ├── routes/          # Flask blueprints
│   │   ├── forms/           # WTForms
│   │   ├── templates/       # Jinja2 templates
│   │   └── main.py          # Flask factory
│   ├── chat/                 # Streamlit chat
│   │   └── app.py
│   ├── scheduler/            # APScheduler jobs
│   │   ├── jobs.py
│   │   └── main.py
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic schemas
│   ├── database/             # Database utilities
│   │   ├── base.py          # Declarative base
│   │   └── session.py       # Session management
│   ├── alembic/             # Database migrations
│   │   └── versions/
│   ├── config.py            # Centralized configuration
│   ├── wsgi_api.py          # API entry point
│   ├── wsgi_app.py          # App entry point
│   └── wsgi_scheduler.py    # Scheduler entry point
├── tests/                    # Test suite (77+ files)
│   ├── conftest.py          # Pytest fixtures
│   ├── ichrisbirch/         # Tests mirror src structure
│   └── test_data/           # Test data generation
├── scripts/                  # Utility scripts
│   ├── postgres_backup.py
│   └── postgres_restore.py
├── deploy-containers/        # Docker deployment
│   └── traefik/             # Traefik configuration
│       ├── certs/           # SSL certificates
│       ├── dynamic/         # Dynamic config
│       └── scripts/         # SSL management
├── docs/                     # MkDocs documentation
├── cli/ichrisbirch          # Main CLI tool
├── docker-compose.yml        # Production config
├── docker-compose.dev.yml    # Development overrides
├── docker-compose.test.yml   # Testing overrides
├── Dockerfile                # Multi-stage build
├── pyproject.toml            # Project dependencies
└── .env                      # Environment variables
```

## Documentation

**Serve locally**: `mkdocs serve` (<http://127.0.0.1:8000>)

**Key docs**:

- [Quick Start](docs/quick-start.md) - Get running in under 5 minutes
- [CLI Usage](docs/cli-traefik-usage.md) - Complete CLI reference
- [Traefik Deployment](docs/traefik-deployment.md) - Reverse proxy configuration
- [Testing Guide](docs/testing/overview.md) - Testing strategy
- [API Documentation](docs/api/index.md) - API reference
- [Troubleshooting](docs/troubleshooting.md) - Common issues

**Auto-generated API docs**:

- FastAPI Swagger UI: <https://api.docker.localhost/docs>
- FastAPI ReDoc: <https://api.docker.localhost/redoc>
