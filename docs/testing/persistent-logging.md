# Test Environment Logging

## Overview

The test stack uses the same stdout-only logging architecture as development and production. All logs go to stdout, and Docker handles persistence via its json-file logging driver. This provides consistent behavior across all environments.

The stack's logs are the e2e suite's. pytest runs the API in-process, so its logs are in its own output, which `./ops/icbops test run` keeps in `.test-reports/pytest-output.log`.

## Viewing Test Logs

### Using the CLI

`ops/log_viewer.py` follows this checkout's stack, renders structlog lines, and reconnects when containers restart:

```bash
# View all test service logs
./ops/icbops testing logs

# View specific service logs
./ops/icbops testing logs api
./ops/icbops testing logs scheduler

# Filter, or print and exit
./ops/icbops testing logs api --level WARNING
./ops/icbops testing logs api --no-follow --tail 100
```

### Using Docker Directly

Each checkout's containers are named `icb-test-<checkout>-<service>`; `./ops/icbops testing status` prints the project name.

```bash
# Follow logs for a specific container
docker logs -f icb-test-<checkout>-api

# View recent logs
docker logs --tail 100 icb-test-<checkout>-api

# View logs since a specific time
docker logs --since 5m icb-test-<checkout>-api
```

## Log Format

Test environment logs use the same structlog format as other environments. The format is controlled by the `LOG_FORMAT` environment variable, which the test stack defaults to `json`. `testing logs` renders either format the same way.

### Console Format

```text
2026-01-13T15:30:45Z [info     ] test_user_created     filename=fixtures.py func_name=setup lineno=45 request_id=abc12345 user_id=1
2026-01-13T15:30:46Z [debug    ] database_query        filename=session.py func_name=execute lineno=89 query=SELECT...
```

### JSON Format (Default)

`LOG_FORMAT=console ./ops/icbops testing restart` switches the stack to console lines. Its default is:

```json
{"timestamp": "2026-01-13T15:30:45Z", "level": "info", "event": "test_user_created", "filename": "fixtures.py", "func_name": "setup", "lineno": 45, "request_id": "abc12345", "user_id": 1}
```

## Request Tracing in Tests

Every API response carries an `X-Request-ID`, and a Playwright trace shows it on each request. The log viewer filters on it:

```bash
./ops/icbops testing logs api --request-id abc12345
```

## Log Persistence

Docker persists logs to disk via the json-file driver. Logs survive container restarts but are removed when containers are removed with `--volumes` flag.

### Accessing Raw Log Files

```bash
# Find log file location for a container
docker inspect icb-test-<checkout>-api --format='{{.LogPath}}'

# View raw log file (requires sudo on Linux)
sudo cat /var/lib/docker/containers/<container-id>/<container-id>-json.log
```

### Log Lifecycle

| Action | Logs Preserved |
| --- | --- |
| `testing restart` | Yes |
| `testing stop` | Yes (until container removed) |
| `testing stop` then `testing start` | Yes |
| Container recreated | No (new container, new logs) |

## Debugging Test Failures

### A pytest failure

The failure and its captured logs are in the run's own output:

```bash
./ops/icbops test run tests/ichrisbirch/api/endpoints/test_tasks.py
less .test-reports/pytest-output.log
jq '.tests[] | select(.outcome == "failed") | .nodeid' .test-reports/pytest-report.json
```

### An e2e failure

The stack stays up after `test e2e`, so its logs are there to read:

```bash
./ops/icbops test e2e e2e/tasks.spec.ts --trace on
./ops/icbops testing logs api --no-follow --level WARNING
npx --prefix frontend playwright show-trace frontend/test-results/<test>/trace.zip
```

## Configuration

### Environment Variables

Test environment logging is configured in `docker-compose.test.yml`:

```yaml
services:
  api:
    environment: !override
      - ENVIRONMENT=testing
      - FASTAPI_DEBUG=False
      - FASTAPI_TESTING=True
      - LOG_FORMAT=${LOG_FORMAT:-json}
      - LOG_LEVEL=${LOG_LEVEL:-DEBUG}
      - LOG_COLORS=${LOG_COLORS:-true}
```

### Log Level for Tests

The stack runs with `LOG_LEVEL=DEBUG` to capture all diagnostic information. Override for less verbose output; compose reads it when the containers are created:

```bash
LOG_LEVEL=INFO ./ops/icbops testing restart
```

## Comparison with Development

| Aspect | Development | Testing |
| --- | --- | --- |
| Log destination | stdout | stdout |
| Persistence | Docker json-file | Docker json-file |
| CLI command | `dev logs` | `testing logs` |
| Watch loop | Yes | Yes |
| Log format | json (default) | json (default) |
| Log level | DEBUG (default) | DEBUG (default) |

## Related Documentation

- [Logging Configuration](../logging-configuration.md) - Full logging architecture details
- [Test Environment Configuration](environment.md) - Test environment setup
- [CLI Management Guide](../cli-traefik-usage.md) - CLI command reference
