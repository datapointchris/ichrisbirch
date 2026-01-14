# Logging Configuration

## Overview

The ichrisbirch application uses **structlog** with a stdout-only architecture. All logs go to stdout, and Docker handles persistence via its logging driver. This is the industry-standard approach for containerized applications.

**Configuration**: `ichrisbirch/logger.py`

```python
LOG_FORMAT = os.environ.get('LOG_FORMAT', 'console')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')
LOG_COLORS = os.environ.get('LOG_COLORS', 'auto')
LOG_FILE = os.environ.get('LOG_FILE', '')
LOG_DIR = os.environ.get('LOG_DIR', '/var/log/ichrisbirch')
```

## Environment Variables

### LOG_FORMAT

Controls the output format for log messages.

| Value | Description | Use Case |
|-------|-------------|----------|
| `console` (default) | Human-readable colored output | Development, debugging |
| `json` | Structured JSON output | Production, log aggregation (ELK, Datadog) |

**Console format example:**

```text
2026-01-13T15:30:45Z [info     ] user_login_success    filename=auth.py func_name=login lineno=45 request_id=abc12345 user_id=123
```

**JSON format example:**

```json
{"timestamp": "2026-01-13T15:30:45Z", "level": "info", "event": "user_login_success", "filename": "auth.py", "func_name": "login", "lineno": 45, "request_id": "abc12345", "user_id": 123}
```

### LOG_LEVEL

Controls which log messages are output.

| Value | Description |
|-------|-------------|
| `DEBUG` (default) | All messages including detailed diagnostics |
| `INFO` | Normal operations (user login, task created, job completed) |
| `WARNING` | Recoverable issues (invalid input, retry attempts) |
| `ERROR` | Failures requiring attention (API errors, DB errors) |
| `CRITICAL` | System-level failures (can't connect to DB) |

### LOG_COLORS

Controls whether colored output is used in console format.

| Value | Description |
|-------|-------------|
| `auto` (default) | Use TTY detection (colors if terminal, no colors if piped) |
| `true` | Force colors on (useful in Docker where TTY detection fails) |
| `false` | Force colors off |

### LOG_FILE

Optional path to a log file for persistence. When set and the directory exists, logs are written to both stdout and the specified file.

| Value | Description |
|-------|-------------|
| Empty (default) | No file logging, stdout only |
| `/var/log/ichrisbirch/api.log` | Write logs to file (and stdout) |

**File logging features:**

- Uses `RotatingFileHandler` to prevent unbounded growth
- Max 25MB per file with 5 backup files (~150MB total per service)
- Plain text format (no ANSI color codes) for easy parsing
- Enables the Admin UI live logs feature

### LOG_DIR

Directory where log files are stored (used by admin UI for log aggregation).

| Value | Description |
|-------|-------------|
| `/var/log/ichrisbirch` (default) | Standard log directory |

**Docker volume mount:**

```yaml
volumes:
  - ichrisbirch_logs:/var/log/ichrisbirch
```

## Request Tracing

All services support request tracing via the `X-Request-ID` header. When a request arrives, middleware generates or extracts a request ID and binds it to structlog's context variables. All subsequent log messages include this ID, enabling correlation across services.

### Request ID Flow

```text
Flask Process                          FastAPI Process
─────────────────                      ─────────────────
1. Request arrives
2. Middleware generates/extracts:
   X-Request-ID: abc12345
3. bind_contextvars(request_id)
4. All Flask logs include request_id
5. API client adds header to request
              │
              └──── HTTP Request ────► 6. Request arrives with header
                                       7. Middleware extracts request_id
                                       8. bind_contextvars(request_id)
                                       9. All FastAPI logs include request_id
```

### Middleware Implementation

**Flask**: `ichrisbirch/app/middleware.py`

```python
class RequestTracingMiddleware:
    def _before_request(self):
        structlog.contextvars.clear_contextvars()
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4())[:8])
        g.request_id = request_id
        structlog.contextvars.bind_contextvars(request_id=request_id)
```

**FastAPI**: `ichrisbirch/api/middleware.py`

```python
class RequestTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        structlog.contextvars.clear_contextvars()
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4())[:8])
        structlog.contextvars.bind_contextvars(request_id=request_id)
        # ...
```

## Viewing Logs

### Development

Use the CLI to view colored logs that persist across container restarts:

```bash
# All services
./cli/ichrisbirch dev logs

# Specific service
./cli/ichrisbirch dev logs api
./cli/ichrisbirch dev logs app
```

The logs command uses a watch loop that automatically reconnects when containers restart.

### Testing

```bash
# View test environment logs
./cli/ichrisbirch testing logs

# Specific service
./cli/ichrisbirch testing logs api
```

### Production

```bash
# View production logs
./cli/ichrisbirch prod logs

# Specific service
./cli/ichrisbirch prod logs api
```

### Direct Docker Commands

```bash
# Follow logs for a specific container
docker logs -f ichrisbirch-api-dev

# View recent logs
docker logs --tail 100 ichrisbirch-api-dev
```

## Log Persistence

Docker handles log persistence via its logging driver. By default, Docker uses the `json-file` driver which stores logs on disk. These logs persist across container restarts.

### Accessing Docker Log Files

```bash
# Find log file location
docker inspect ichrisbirch-api-dev --format='{{.LogPath}}'

# View raw log file (requires sudo)
sudo cat /var/lib/docker/containers/<container-id>/<container-id>-json.log
```

### Log Rotation

Docker manages log rotation. Configure in Docker daemon settings if needed:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

## Structlog Configuration

**Configuration file**: `ichrisbirch/logger.py:42-75`

The structlog configuration includes:

1. **Context variable merging**: Includes request_id and other bound context
2. **Log level filtering**: Based on LOG_LEVEL environment variable
3. **Timestamp**: ISO 8601 format (UTC)
4. **Call site tracking**: Automatic filename, function name, and line number
5. **Stack info rendering**: For exception tracebacks
6. **Format rendering**: Console or JSON based on LOG_FORMAT

### Processor Chain

```python
processors = [
    structlog.contextvars.merge_contextvars,      # Include request_id, etc.
    structlog.processors.add_log_level,           # Add level field
    structlog.processors.TimeStamper(...),        # Add timestamp
    CallsiteParameterAdder({...}),                # Add filename, func, line
    structlog.processors.StackInfoRenderer(),     # Render stack traces
    structlog.processors.format_exc_info,         # Format exceptions
    # Final renderer: ConsoleRenderer or JSONRenderer
]
```

## Third-Party Logger Suppression

Noisy third-party loggers are suppressed to reduce log noise:

**Configuration**: `ichrisbirch/logger.py:78-101`

| Logger | Level | Reason |
|--------|-------|--------|
| `apscheduler` | WARNING | Verbose job scheduling messages |
| `httpx` | WARNING | HTTP client request details |
| `werkzeug` | WARNING | Flask development server messages |
| `boto3`, `botocore` | INFO | AWS SDK details |
| `sqlalchemy_json` | INFO | JSON field operations |

## Usage Pattern

Every module uses the same simple pattern:

```python
import structlog

logger = structlog.get_logger()

# Log with structured data
logger.info('user_login_success', user_id=user.id, email=user.email)
logger.error('database_error', error=str(e), operation='create_user')
```

### Event Naming Convention

Use snake_case event names that describe what happened:

| Good | Bad |
|------|-----|
| `user_login_success` | `logged in user` |
| `task_created` | `Created new task` |
| `api_request_failed` | `HTTP error` |
| `job_started` | `Starting job...` |

## Migration from Standard Logging

The project migrated from Python's standard logging module to structlog. Key differences:

| Standard Logging | Structlog |
|------------------|-----------|
| `logger = logging.getLogger(__name__)` | `logger = structlog.get_logger()` |
| `logger.info(f'User {user_id} logged in')` | `logger.info('user_login', user_id=user_id)` |
| String interpolation | Keyword arguments |
| `__name__` for logger identification | CallsiteParameterAdder for location |

## Benefits

1. **Structured data**: All log data is structured, enabling filtering and analysis
2. **Request tracing**: Correlate logs across services with request_id
3. **Consistent format**: Same output format across all services
4. **Environment flexibility**: Switch between console and JSON with one variable
5. **No file management**: Docker handles persistence and rotation
6. **Industry standard**: Follows 12-factor app logging principles

## Admin UI Integration

When `LOG_FILE` is configured, the admin dashboard provides live log viewing capabilities.

### Live Logs Feature

The admin UI at `/admin/logs/` provides real-time log streaming via WebSocket:

- **WebSocket endpoint**: `wss://api.docker.localhost/admin/log-stream/`
- **Authentication**: JWT cookie-based (set automatically on Flask login)
- **Admin-only**: Requires admin user privileges
- **ANSI stripping**: Color codes removed for clean browser display
- **Client-side colorization**: JavaScript re-applies colors based on log level

### Log Graphs Feature

The admin UI at `/admin/log-graphs/` provides log analytics:

- Reads all `*.log` files from `LOG_DIR`
- Parses structlog format into structured data
- Generates charts for log levels, timestamps, and sources
- Useful for identifying patterns and issues

### Docker Configuration

To enable file logging in Docker Compose:

```yaml
api:
  environment:
    - LOG_FILE=/var/log/ichrisbirch/api.log
  volumes:
    - ichrisbirch_logs:/var/log/ichrisbirch

app:
  environment:
    - LOG_FILE=/var/log/ichrisbirch/app.log
  volumes:
    - ichrisbirch_logs:/var/log/ichrisbirch
```

All services share the same log volume, allowing the admin UI to aggregate logs from all services.
