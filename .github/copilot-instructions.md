# AI Coding Agent Instructions for iChrisBirch

## 🎯 PROFESSIONAL DEVELOPMENT STANDARDS 🎯

**You are a professional Python developer with expert-level knowledge and must write production-quality code that follows industry standards and conventions.**

**Code Quality Requirements**:

- Follow PEP 8 style guidelines and Python best practices
- Write clean, readable, maintainable code with meaningful variable names
- Use proper type hints for functions unless the type hint will be complex or Any
- Write docstrings in the Google style format for all public functions and classes, unless they are simple and the docstring would be superfluous
- Implement proper error handling with specific exceptions rather than broad catches
- Every piece of code must pass a rigorous code review - no hacky solutions or quick fixes
- Fail fast and explicit is better than hidden defaults or defensive coding in business logic

**Investigation Protocol**:

- When something is not working, STOP and investigate the root cause thoroughly
- Do NOT change unrelated components without understanding why they might be affected
- Examine existing tooling and patterns BEFORE making changes
- Follow the principle: "First understand, then fix"
- Document your investigation process and findings in a technical documentation style, not storytelling

**Code Review Process**:

- After completing any substantial changes, review your work for improvements
- Look for opportunities to enhance clarity, performance, or maintainability
- Refactor immediately if you identify better patterns or approaches
- Ensure all changes align with existing codebase patterns and conventions

## ⚠️ CRITICAL RULE - ENVIRONMENT VARIABLES ⚠️

### ABSOLUTELY NEVER EVER ADD ENVIRONMENT VARIABLES ANYWHERE UNDER ANY CIRCUMSTANCES

- DO NOT add environment variables to Docker Compose files
- DO NOT add environment variables to .env files
- DO NOT add environment variables to any configuration files
- DO NOT suggest adding environment variables as a solution
- DO NOT add any new environment variables to SSM Parameters either
- Environment variables are managed through existing SSM parameters and configuration patterns ONLY
- If configuration is missing, it is an SSM parameter issue, NOT something to solve with random environment variables
- This rule has NO exceptions - follow existing configuration patterns ONLY

**For SSM Debugging**: Use `scripts/get_ssm_parameters.py --env {development|testing|production}` to view current SSM parameters for debugging configuration issues. This script is for READ-ONLY debugging purposes only - never use it as justification to add new parameters.

## Architecture Overview

This is a **containerized dual-application architecture** with strict separation between frontend and backend:

- **Flask App** (`ichrisbirch/app/`): Web frontend with forms, templates, authentication
- **FastAPI Backend** (`ichrisbirch/api/`): Independent REST API with database access
- **PostgreSQL Database**: Containerized database service

## 🚨 CRITICAL DOCKER & TESTING PORT CONFIGURATION 🚨

**DOCKER COMPOSE SERVICES USE DEFAULT PORTS INTERNALLY**:

- Flask App: Port 5000 (internal container communication)
- FastAPI Backend: Port 8000 (internal container communication)
- PostgreSQL Database: Port 5432 (internal container communication)
- Nginx: Port 80 (internal container communication)

**TESTS RUN ON HOST AND CONNECT TO EXTERNAL PORTS**:

- Flask App: localhost:5001 (external host access)
- FastAPI Backend: localhost:8001 (external host access)
- PostgreSQL Database: localhost:5434 (external host access)
- Nginx: localhost:8080 (external host access)

**DO NOT WASTE TIME ON PORT "ISSUES"**:

- Docker Compose logs will show default ports (5000, 8000, 5432) - this is CORRECT
- Tests connect to external ports (5001, 8001, 5434) - this is CORRECT
- This is NOT a Docker Compose configuration problem
- This is NOT an environment variable problem
- This is NOT a missing configuration problem
- The port mapping is: `external_port:internal_port` in docker-compose files

**Port Mapping Examples**:

```yaml
# In docker-compose files
flask:
  ports:
    - "5001:5000"  # external:internal
fastapi:
  ports:
    - "8001:8000"  # external:internal
postgres:
  ports:
    - "5434:5432"  # external:internal
```

- **Nginx**: Reverse proxy and static file serving
- **All services orchestrated via Docker Compose** with environment-specific compose files
- **Critical Rule**: Flask NEVER accesses database directly - all data flows through API calls via `LoggingAPIClient`

## Settings & Configuration Pattern

**Simplified containerized configuration**:

- Single `Settings` class instantiated once in `ichrisbirch/config.py`
- Environment variables injected via Docker Compose files
- Different compose files for dev/test/prod: `docker-compose.dev.yml`, `docker-compose.test.yml`, `docker-compose.prod.yml`
- **No more environment-specific settings files** - settings resolved once at startup
- **NEVER create additional .env files** - use existing configuration patterns only
- **NEVER add random environment variables** - if configuration is missing, it's usually an SSM parameter issue or the SSM parameter name doesn't match expectations
- Import `settings` directly everywhere: `from ichrisbirch.config import settings`

```python
# Standard pattern - import settings directly
from flask import current_app
from ichrisbirch.api.client.logging_client import logging_flask_session_client
from ichrisbirch import schemas

settings = current_app.config['SETTINGS']
with logging_flask_session_client(base_url=settings.api_url) as client:
    habits_api = client.resource('habits', schemas.Habit)
    habits = habits_api.get_many(params={'current': True})
```

## Flask-to-API Communication Pattern

**Architecture**:

- **LoggingAPIClient** (`ichrisbirch/api/client/logging_client.py`): Main client with extensive logging, session management, and resource clients
- **Factory Functions**: `logging_flask_session_client()` for user auth, `logging_internal_service_client()` for internal service auth

**Authentication Strategy**:

- **User Operations**: Use `logging_flask_session_client()` - authenticates as the logged-in Flask user
- **Internal Service**: Use `logging_internal_service_client()` - for system operations (user lookups, scheduled jobs, etc.)
- **API Endpoint Security**: Users endpoints require specific auth - regular users get own info, admins/internal service can list all

**Standard Pattern for Flask Routes**:

```python
# User-authenticated operations (most common)
from flask import current_app
from ichrisbirch.api.client.logging_client import logging_flask_session_client
from ichrisbirch import schemas

def some_route():
    settings = current_app.config['SETTINGS']
    with logging_flask_session_client(base_url=settings.api_url) as client:
        habits_api = client.resource('habits', schemas.Habit)
        habits = habits_api.get_many(params={'current': True})
```

**Internal Service Authentication Pattern**:

```python
# For system operations that don't need user context
from flask import current_app
from ichrisbirch.api.client.logging_client import logging_internal_service_client
from ichrisbirch import schemas

def admin_operation():
    settings = current_app.config['SETTINGS']
    with logging_internal_service_client(base_url=settings.api_url) as client:
        users_api = client.resource('users', schemas.User)
        all_users = users_api.get_many()
```

**Preserved Functionality Requirements**:

- Keep extensive logging and debugging capabilities
- Maintain custom methods like `get_generic()`, `post_action()`
- Preserve existing utility functions like `utils.url_builder()`

**Authentication options**:

- **User Auth**: `X-User-ID` + `X-Application-ID` headers (existing pattern)
- **Internal Service**: `X-Internal-Service` + `X-Service-Key` headers (new option)
- **JWT Tokens**: Standard Bearer tokens for external clients

## Database & Testing

- **SQLAlchemy models** in `ichrisbirch/models/` with shared schemas in `ichrisbirch/schemas/`
- **Test isolation**: Each test module has `@pytest.fixture(autouse=True)` for data setup/teardown
- **Database sessions**: Use generators with context managers (`get_sqlalchemy_session()`)

```python
@pytest.fixture(autouse=True)
def insert_testing_data():
    insert_test_data('habits', 'habitcategories')
    yield
    delete_test_data('habits', 'habitcategories')
```

## FastAPI Endpoint Patterns

**Consistent structure** across all endpoints:

- Dependency injection for database sessions and current user
- CRUD operations with standard response models
- Path parameter order: `/resource/{id}/action/` (not `/resource/action/{id}/`)

```python
@router.get('/{id}/', response_model=schemas.Habit, status_code=status.HTTP_200_OK)
async def read_one(id: int, session: Session = Depends(get_sqlalchemy_session)):
    if habit := session.get(models.Habit, id):
        return habit
    raise NotFoundException("habit", id, logger)
```

## Frontend Structure

- **Blueprint organization**: Each app has its own blueprint in `ichrisbirch/app/routes/`
- **Template inheritance**: App-specific base templates extend global `base.html`
- **Form handling**: POST actions use `action` field to determine operation type
- **CSS**: SASS architecture with page-specific files and BEM-like naming

## Development Workflows

**Virtual Environment Activation**: When running any project commands locally (outside of Docker), ALWAYS activate the virtual environment first:

```bash
# For UV-based virtual environment (current standard)
source .venv/bin/activate  # or `. .venv/bin/activate`

# Then run project commands
python -m pytest
python -m ichrisbirch.wsgi_api
uv run python script.py

# Alternative: Use UV run (preferred for single commands)
uv run pytest
uv run python -m ichrisbirch.wsgi_api
```

**Local Development**:

```bash
# Start dev environment
docker-compose -f docker-compose.dev.yml up -d

# Run tests with test environment
docker-compose -f docker-compose.test.yml up -d
pytest -vv --cov=ichrisbirch

# Production deployment
docker-compose -f docker-compose.prod.yml up -d
```

**Container Services**:

- Flask App: Web frontend service
- FastAPI Backend: API service
- PostgreSQL: Database service
- Nginx: Reverse proxy service

**Key directories**:

- `ichrisbirch/api/endpoints/` - FastAPI route definitions
- `ichrisbirch/app/routes/` - Flask blueprints
- `ichrisbirch/models/` - SQLAlchemy database models
- `ichrisbirch/schemas/` - Pydantic API schemas
- `tests/ichrisbirch/api/endpoints/` - API endpoint tests
- `tests/ichrisbirch/app/routes/` - Flask route tests

## Common Patterns

**Adding new features** (see `docs/add_new_app.md`):

1. Create model in `ichrisbirch/models/`
2. Create schemas in `ichrisbirch/schemas/`
3. Create API endpoints in `ichrisbirch/api/endpoints/`
4. Create Flask routes in `ichrisbirch/app/routes/`
5. Register blueprints in `ichrisbirch/app/main.py`
6. Add API routes in `ichrisbirch/api/main.py`

**CRUD testing**: Use `ApiCrudTester` class for consistent API endpoint testing
**Frontend testing**: Playwright tests in `tests/ichrisbirch/frontend/`

## Critical Gotchas

1. **Virtual Environment Required** - Always activate virtual environment or use `uv run` when running project commands locally
2. **No database access in Flask** - Always use `LoggingAPIClient` with appropriate auth method
3. **Preserve existing patterns** - Use existing utility functions like `utils.url_builder()`, prefer not to replace with stdlib unless there is a compelling reason
4. **Authentication method choice** - Use `logging_internal_service_client()` for system operations, `logging_flask_session_client()` for user operations
5. **Docker Compose environments** - Use correct compose file for target environment
6. **Custom client methods** - `get_generic()`, `post_action()` are intentional patterns, preserve them
7. **Module-level imports only** - Never use function-level imports; all imports must be at the module level to maintain code clarity and avoid import-related issues

## Development Principles

**Development Principles**: Always prefer existing utility functions and patterns unless they cause errors or interfere with functionality. Examples:

- Use `utils.url_builder()` instead of `urllib.parse.urljoin`
- Keep custom client methods like `get_generic()` and `post_action()`
- Preserve extensive logging patterns for debugging
- Maintain backwards compatibility when improving architecture

**NO Defensive Coding**: Do NOT add inline defaults, fallbacks, or defensive checks scattered throughout the codebase:

- ❌ WRONG: `getattr(settings.auth, 'key', 'default')` inside business logic
- ✅ RIGHT: `settings.auth.key` - let it fail fast if misconfigured
- Application should fail at startup if configuration is missing, not hide problems with random defaults
- Defensive coding belongs in config validation, not scattered throughout the project
- Think like a professional: fail fast and explicit is better than hidden defaults

**Function Enhancement Strategy**: When improving functionality:

1. Enhance existing classes/functions rather than replacing them
2. Add optional parameters to maintain backwards compatibility
3. Preserve all custom methods that existing code relies on
4. Keep detailed logging and debugging capabilities intact

**Pattern Consistency**: Always follow established patterns in the codebase:

- Use `os.environ['KEY']` in config.py (not `os.environ.get()` with defaults)
- Use existing utility functions like `utils.url_builder()` instead of stdlib equivalents
- Follow existing naming conventions and code organization
- Maintain consistent import patterns and module structure

**Documentation Standards**: All documentation and help text must be written for technical developers:

- Use precise technical language, not marketing speak
- Explain the "why" behind commands and options
- Include technical details like ports, file paths, and service dependencies
- Document command behavior differences (e.g., restart vs rebuild)
- Avoid feature summaries; focus on implementation details and usage patterns
- Include troubleshooting information and technical constraints

**Troubleshooting Documentation**: When resolving any issue, ALWAYS document it in the troubleshooting section:

- Add issues to appropriate troubleshooting page in `docs/troubleshooting/`
- Include the complete problem description with error messages
- Document root cause analysis explaining WHY the issue occurred
- List ALL attempted solutions that didn't work with explanations of why they failed
- Provide the final working solution with complete code examples
- Add prevention strategies to avoid the issue in the future
- Use proper markdown formatting with code blocks and admonitions
- Follow the established troubleshooting documentation format:

```markdown
  ### Issue Title

  **Problem:** Clear description of the issue

  **Error Messages:**

  Actual error output  **Root Cause:** Technical explanation of why it happened

  **Attempted Solutions (That Failed):**
  - What we tried and why it didn't work

  **Resolution:** Working solution with code examples

  **Prevention:** How to avoid this in the future


  **Prevention:** How to avoid this in the future

- Update the troubleshooting index page with links to new issues
- This ensures all problem-solving knowledge is preserved for future reference
```
