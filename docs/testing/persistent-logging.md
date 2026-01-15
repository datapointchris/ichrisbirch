# Test Environment Logging

## Overview

The test environment uses the same stdout-only logging architecture as development and production. All logs go to stdout, and Docker handles persistence via its json-file logging driver. This provides consistent behavior across all environments.

## Viewing Test Logs

### Using the CLI

The CLI provides persistent log viewing that automatically reconnects when containers restart:

```bash
# View all test service logs
./cli/ichrisbirch testing logs

# View specific service logs
./cli/ichrisbirch testing logs api
./cli/ichrisbirch testing logs app
./cli/ichrisbirch testing logs chat
./cli/ichrisbirch testing logs scheduler
```

The logs command uses a watch loop (`cli/ichrisbirch:316-324`) that:

- Follows logs in real-time
- Automatically reconnects when containers restart
- Colorizes service names for readability
- Press Ctrl+C to exit

### Using Docker Directly

```bash
# Follow logs for a specific container
docker logs -f icb-test-api

# View recent logs
docker logs --tail 100 icb-test-api

# View logs since a specific time
docker logs --since 5m icb-test-api
```

## Log Format

Test environment logs use the same structlog format as other environments. The format is controlled by the `LOG_FORMAT` environment variable (default: `console`).

### Console Format (Default)

```text
2026-01-13T15:30:45Z [info     ] test_user_created     filename=fixtures.py func_name=setup lineno=45 request_id=abc12345 user_id=1
2026-01-13T15:30:46Z [debug    ] database_query        filename=session.py func_name=execute lineno=89 query=SELECT...
```

### JSON Format

Set `LOG_FORMAT=json` in docker-compose.test.yml to enable:

```json
{"timestamp": "2026-01-13T15:30:45Z", "level": "info", "event": "test_user_created", "filename": "fixtures.py", "func_name": "setup", "lineno": 45, "request_id": "abc12345", "user_id": 1}
```

## Request Tracing in Tests

Test logs include request IDs for tracing requests across services. When running integration tests that call the API through HTTP, you can trace the full request flow:

```bash
# Make a request and note the request_id in logs
curl -v https://api.test.localhost:8443/tasks/
# Response includes: X-Request-ID: abc12345

# Search logs for that request
./cli/ichrisbirch testing logs | grep abc12345
```

## Log Persistence

Docker persists logs to disk via the json-file driver. Logs survive container restarts but are removed when containers are removed with `--volumes` flag.

### Accessing Raw Log Files

```bash
# Find log file location for a container
docker inspect icb-test-api --format='{{.LogPath}}'

# View raw log file (requires sudo on Linux)
sudo cat /var/lib/docker/containers/<container-id>/<container-id>-json.log
```

### Log Lifecycle

| Action | Logs Preserved |
|--------|----------------|
| `testing restart` | Yes |
| `testing stop` | Yes (until container removed) |
| `testing stop` then `testing start` | Yes |
| Container recreated | No (new container, new logs) |

## Debugging Test Failures

### Viewing Logs During Test Run

When using `test run`, containers stay running after tests complete. View logs immediately:

```bash
# Run tests
./cli/ichrisbirch test run tests/ichrisbirch/api/test_tasks.py

# View logs after failure
./cli/ichrisbirch testing logs api
```

### Correlating Test Failures with Logs

1. Run tests with verbose output to get timestamps:

   ```bash
   ./cli/ichrisbirch test run -v
   ```

2. View logs around the failure time:

   ```bash
   docker logs --since 1m icb-test-api
   ```

3. Search for error events:

   ```bash
   ./cli/ichrisbirch testing logs | grep -i error
   ```

## Configuration

### Environment Variables

Test environment logging is configured in `docker-compose.test.yml`:

```yaml
services:
  api:
    environment:
      - LOG_FORMAT=${LOG_FORMAT:-console}
      - LOG_LEVEL=${LOG_LEVEL:-DEBUG}
      - LOG_COLORS=true  # Force colors in containers
```

### Log Level for Tests

Tests typically run with `LOG_LEVEL=DEBUG` to capture all diagnostic information. Override for less verbose output:

```bash
LOG_LEVEL=INFO ./cli/ichrisbirch test run
```

## Comparison with Development

| Aspect | Development | Testing |
|--------|-------------|---------|
| Log destination | stdout | stdout |
| Persistence | Docker json-file | Docker json-file |
| CLI command | `dev logs` | `testing logs` |
| Watch loop | Yes | Yes |
| Log format | console (default) | console (default) |
| Log level | DEBUG (default) | DEBUG (default) |

## Related Documentation

- [Logging Configuration](../logging-configuration.md) - Full logging architecture details
- [Test Environment Configuration](environment.md) - Test environment setup
- [CLI Management Guide](../cli-traefik-usage.md) - CLI command reference
