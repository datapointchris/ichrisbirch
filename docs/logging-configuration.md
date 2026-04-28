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

| Value | Description |
| --- | --- |
| `console` | Human-readable colored output |
| `json` | Structured JSON output |

`json` is the default for dev, test, and production and is required by the
CLI viewer (`cli/log_viewer.py`) and by Loki's pipeline. The dev and test
compose files set `LOG_FORMAT=${LOG_FORMAT:-json}` so the viewer always
receives structured input. Override per-service by exporting
`LOG_FORMAT=console` for raw colored output without the viewer.

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
| --- | --- |
| `DEBUG` (default) | All messages including detailed diagnostics |
| `INFO` | Normal operations (user login, task created, job completed) |
| `WARNING` | Recoverable issues (invalid input, retry attempts) |
| `ERROR` | Failures requiring attention (API errors, DB errors) |
| `CRITICAL` | System-level failures (can't connect to DB) |

### LOG_COLORS

Controls whether colored output is used in console format.

| Value | Description |
| --- | --- |
| `auto` (default) | Use TTY detection (colors if terminal, no colors if piped) |
| `true` | Force colors on (useful in Docker where TTY detection fails) |
| `false` | Force colors off |

### LOG_FILE

Optional path to a log file for persistence. When set and the directory exists, logs are written to both stdout and the specified file.

| Value | Description |
| --- | --- |
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
| --- | --- |
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
Vue SPA (browser)                       FastAPI Process
─────────────────                       ─────────────────
1. Vue API client generates
   X-Request-ID: abc12345 per request
   (frontend/src/api/client.ts)
              │
              └──── HTTP Request ────► 2. Middleware extracts request_id
                                          (or generates one if missing)
                                       3. bind_contextvars(request_id)
                                       4. All FastAPI logs include request_id
                                       5. Header echoed on the response
   ◀── X-Request-ID: abc12345 ────────────────────────
6. Vue captures response header
   into ApiError for surfacing in UI
```

### Middleware Implementation

**FastAPI**: `ichrisbirch/api/middleware.py`

```python
class RequestTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        structlog.contextvars.clear_contextvars()
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4())[:8])
        structlog.contextvars.bind_contextvars(request_id=request_id)
        # ...
```

### Scheduler Job Correlation

Scheduler jobs are not request-scoped, so they get their own correlation token.
The `@job_logger` decorator in `ichrisbirch/scheduler/jobs.py` generates a
per-invocation `job_run_id` (8-hex), binds it into structlog contextvars for
the lifetime of the job, and persists it on the `SchedulerJobRun` row written
at the end. Every log line a job emits carries the `job_run_id`, so a single
execution is queryable in Loki via `{job_run_id="..."}` and joins back to the
DB record by the same id.

## Viewing Logs

### Development

Use the CLI to view colored logs that persist across container restarts:

```bash
# All services
./cli/icb dev logs

# Specific service
./cli/icb dev logs api
./cli/icb dev logs scheduler
./cli/icb dev logs vue
```

The logs command uses a watch loop that automatically reconnects when containers restart, and supports filter flags described in [CLI Usage](cli-traefik-usage.md).

### Testing

```bash
# View test environment logs
./cli/icb testing logs

# Specific service
./cli/icb testing logs api
```

### Production

```bash
# View production logs
./cli/icb prod logs

# Specific service
./cli/icb prod logs api
```

### Direct Docker Commands

```bash
# Follow logs for a specific container
docker logs -f icb-dev-api

# View recent logs
docker logs --tail 100 icb-dev-api
```

## Log Persistence

Docker handles log persistence via its logging driver. By default, Docker uses the `json-file` driver which stores logs on disk. These logs persist across container restarts.

### Accessing Docker Log Files

```bash
# Find log file location
docker inspect icb-dev-api --format='{{.LogPath}}'

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
| --- | --- | --- |
| `apscheduler` | WARNING | Verbose job scheduling messages |
| `httpx` | WARNING | HTTP client request details |
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
| --- | --- |
| `user_login_success` | `logged in user` |
| `task_created` | `Created new task` |
| `api_request_failed` | `HTTP error` |
| `job_started` | `Starting job...` |

## Migration from Standard Logging

The project migrated from Python's standard logging module to structlog. Key differences:

| Standard Logging | Structlog |
| --- | --- |
| `logger = logging.getLogger(__name__)` | `logger = structlog.get_logger()` |
| `logger.info(f'User {user_id} logged in')` | `logger.info('user_login', user_id=user_id)` |
| String interpolation | Keyword arguments |
| `__name__` for logger identification | CallsiteParameterAdder for location |

## Vue Frontend Logging

The Vue 3 frontend uses **consola** with custom structured reporters that match structlog's output format. This ensures consistent log format across Python and JavaScript services for Loki aggregation.

**Configuration**: `frontend/src/utils/logger.ts`

### Vue Logger Usage

```typescript
import { createLogger } from '@/utils/logger'

const logger = createLogger('CountdownsStore')

// Log with structured data (matches structlog's keyword arguments)
logger.info('countdown_created', { id: data.id, name: data.name })
logger.error('countdown_create_failed', { detail: error.detail, status: error.status })
```

### Output Formats

**Dev (key=value, matching structlog console format)**:

```text
2026-03-13T15:30:45.123Z [info   ] countdown_created              module=CountdownsStore id=42 name="Summer Trip"
```

**Production (JSON, in browser DevTools only)**:

```json
{"timestamp":"2026-03-13T15:30:45.123Z","level":"info","event":"countdown_created","module":"CountdownsStore","id":42,"name":"Summer Trip"}
```

In production the JSON reporter calls `console.info(JSON.stringify(...))`, so
the entry lands in the user's browser DevTools and nowhere else. There is no
shipping pipeline today — Vue is a static SPA in production, so its logs
never reach a container that Promtail can scrape. Cross-service log shipping
for the browser is planned via OpenTelemetry; see `.planning/otel-rum.md`.

### Vue Request Tracing

The Vue API client (`frontend/src/api/client.ts`) adds `X-Request-ID` headers to every outgoing request via an Axios interceptor. This ID is logged in the browser console (consola) and on the server (structlog), enabling correlation when reading both sides simultaneously. End-to-end correlation in a single query becomes possible once the OTel work in `.planning/otel-rum.md` lands.

### Log Level Control

In development, you can change the log level at runtime via the browser console:

```javascript
window.__setLogLevel('debug')  // Show all logs
window.__setLogLevel('error')  // Errors only
```

## Benefits

1. **Structured data**: All log data is structured, enabling filtering and analysis
2. **Request tracing**: Correlate logs across services with request_id
3. **Consistent format**: Same output format across all services (Python + Vue)
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

scheduler:
  environment:
    - LOG_FILE=/var/log/ichrisbirch/scheduler.log
  volumes:
    - ichrisbirch_logs:/var/log/ichrisbirch

chat:
  environment:
    - LOG_FILE=/var/log/ichrisbirch/chat.log
  volumes:
    - ichrisbirch_logs:/var/log/ichrisbirch
```

All services share the same log volume, allowing the admin UI to aggregate logs from all services.
