# Admin Dashboard

The admin dashboard provides administrative features for monitoring and managing the ichrisbirch application.

## Access

**URL:** `https://app.docker.localhost/admin/` (development)

**Requirements:**

- Must be logged in as an admin user
- Admin users have `is_admin=True` in the database

## Features

### Live Logs

**URL:** `/admin/logs/`

Real-time log streaming from all services via WebSocket.

#### How It Works

1. **Flask login sets JWT cookie:** When you log in via the Flask app, a JWT token is requested from the API and stored as a cookie on the parent domain (e.g., `docker.localhost`)

2. **WebSocket connects with cookie auth:** The JavaScript WebSocket client connects to `wss://api.docker.localhost/admin/log-stream/`. The browser automatically sends the `access_token` cookie.

3. **API validates JWT and streams logs:** The WebSocket endpoint validates the JWT token, checks for admin privileges, then streams log lines from all services.

#### Technical Details

- **WebSocket endpoint:** `/admin/log-stream/`
- **Authentication:** JWT cookie (`access_token`)
- **Admin check:** User must have `is_admin=True`
- **Log source:** Reads from `LOG_DIR` (default: `/var/log/ichrisbirch`)
- **ANSI stripping:** Color codes removed server-side for clean transmission
- **Client colorization:** JavaScript re-applies colors based on log level

#### Log Format

Logs use structlog's ConsoleRenderer format:

```text
2026-01-14T08:14:21Z [info     ] user_login_success    filename=auth.py func_name=login lineno=45 user_id=123
```

The client-side JavaScript colorizes log levels:

- `[debug   ]` - Green
- `[info    ]` - Light blue
- `[warning ]` - Yellow
- `[error   ]` - Red
- `[critical]` - Magenta

### Log Graphs

**URL:** `/admin/log-graphs/`

Analytics and visualization of log data.

#### Capabilities

- Reads all `*.log` files from `LOG_DIR`
- Parses structlog format into structured data with Polars
- Generates charts showing:
  - Log count by level
  - Log timeline
  - Logs by source file
  - Error patterns

#### Data Schema

Each log line is parsed into:

| Field | Type | Description |
|-------|------|-------------|
| `log_level` | Categorical | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `timestamp` | Datetime | When the log was created |
| `filename` | String | Source file name |
| `func_name` | String | Function that logged |
| `lineno` | Int16 | Line number |
| `message` | String | Log message/event |
| `source` | String | Log file source (api, app, scheduler, etc.) |

### Traefik Dashboard

**Development URL:** `https://dashboard.docker.localhost/`
**Credentials:** `dev` / `devpass`

**Test URL:** `https://dashboard.test.localhost:8443/`
**Credentials:** `test` / `testpass`

The Traefik dashboard provides:

- Real-time router and service status
- Request/response metrics
- Health check status
- Configuration details

## Configuration

### Enabling File Logging

For the live logs feature to work, services must write to log files:

```yaml
# docker-compose.dev.yml
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

### JWT Cookie for WebSocket Auth

The JWT cookie is automatically set when logging into the Flask app:

```python
# ichrisbirch/app/routes/auth.py
response.set_cookie(
    'access_token',
    f'Bearer {access_token}',
    httponly=True,
    secure=request.is_secure,
    samesite='Lax',
    domain=parent_domain,  # e.g., 'docker.localhost'
)
```

The cookie is set on the parent domain to allow cross-subdomain access (app.docker.localhost → api.docker.localhost).

## Troubleshooting

### Live Logs Not Showing

1. **Check LOG_FILE is set:** Verify the environment variable is configured in docker-compose
2. **Check volume mount:** Ensure `ichrisbirch_logs` volume is mounted to `/var/log/ichrisbirch`
3. **Check admin access:** Verify you're logged in as an admin user
4. **Check browser console:** Look for WebSocket connection errors

### WebSocket Connection Failed

1. **Check JWT cookie:** Open browser DevTools → Application → Cookies → Look for `access_token`
2. **Check cookie domain:** Cookie should be on parent domain (e.g., `docker.localhost`)
3. **Re-login:** Log out and log back in to refresh the JWT cookie
4. **Check Traefik:** Ensure Traefik is routing WebSocket connections correctly

### Log Graphs Empty

1. **Check LOG_DIR exists:** The directory `/var/log/ichrisbirch` must exist and contain `.log` files
2. **Check log format:** Logs must be in structlog ConsoleRenderer format
3. **Check file permissions:** The app user must be able to read the log files

## API Endpoints

### WebSocket Log Stream

```yaml
GET wss://api.docker.localhost/admin/log-stream/
```

**Authentication:** `access_token` cookie with valid JWT

**Response:** Stream of log lines (one per WebSocket message)

**Close codes:**

- `1008` (Policy Violation): No token, invalid token, or non-admin user
- `1000` (Normal): Client disconnected

### Log Graphs Data

The log graphs page uses server-side rendering with Polars DataFrames, so there's no separate API endpoint for the data.
