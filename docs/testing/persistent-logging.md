# Test Environment Persistent Logging

## Overview

The test environment includes persistent logging that mounts directly to your local file system for immediate access. Logs are stored in `$ICHRISBIRCH_HOME/test-logs/` and can be viewed using the enhanced CLI commands with full color support and real-time tailing capabilities.

## Architecture

### Local Directory Structure

- **Local Path**: `$ICHRISBIRCH_HOME/test-logs/`  
- **Container Path**: `/var/log/ichrisbirch/` (inside containers)
- **Volume Type**: Bind mount (direct file system access)
- **Log Files**:
  - `api.log` - FastAPI service logs
  - `app.log` - Flask app logs  
  - `chat.log` - Streamlit chat service logs
  - `scheduler.log` - Background scheduler logs
  - `redis.log` - Redis server logs

### How It Works

1. **Bind Mount Volume**: Docker volume directly mounts to `test-logs/` directory
2. **Log Initialization Service**: Temporary `log-init` container creates log files with proper permissions  
3. **Environment Variable**: Each service gets `LOG_FILE_PATH=/var/log/ichrisbirch/{service}.log`
4. **Dynamic File Handler**: Logger automatically adds file logging when `LOG_FILE_PATH` is set
5. **Direct File Access**: Logs are immediately accessible on the host file system

## Configuration

### Docker Compose Changes

Each test service now includes:

```yaml
environment:
  - LOG_FILE_PATH=/var/log/ichrisbirch/{service}.log
volumes:
  - ichrisbirch_testing_logs:/var/log/ichrisbirch
depends_on:
  log-init:
    condition: service_completed_successfully
```

### Logger Enhancement

The logger in `ichrisbirch/logger.py` now dynamically adds a file handler:

```python
# Add file handler if LOG_FILE_PATH is set (for test environment persistent logging)
if log_file_path := os.environ.get('LOG_FILE_PATH'):
    HANDLERS['file'] = {
        'formatter': 'enhanced',
        'class': 'logging.handlers.RotatingFileHandler',
        'maxBytes': 10_000_000,
        'backupCount': 3,
        'filename': log_file_path,
    }
```

## Usage

### Starting Test Environment

```bash
ichrisbirch testing start
```

Logs will be written to both:

- **Console**: Standard Docker Compose logs (`docker-compose logs`)
- **Local Files**: Directly accessible at `$ICHRISBIRCH_HOME/test-logs/`

### Viewing Persistent Logs via CLI

#### Basic Log Viewing

```bash
# View all logs (last 100 lines each)
ichrisbirch testing app-logs

# View specific service logs
ichrisbirch testing app-logs api
ichrisbirch testing app-logs app
ichrisbirch testing app-logs chat  
ichrisbirch testing app-logs scheduler
ichrisbirch testing app-logs redis

# Show more/fewer lines
ichrisbirch testing app-logs api 50
ichrisbirch testing app-logs all 200
```

#### Real-Time Log Following

```bash
# Follow specific service logs
ichrisbirch testing app-logs api --follow
ichrisbirch testing app-logs app 0 --follow

# Follow ALL logs simultaneously (recommended!)
ichrisbirch testing app-logs-follow all

# Follow specific service with dedicated command
ichrisbirch testing app-logs-follow api
```

#### Enhanced Multi-Log Viewing

For the best experience viewing all logs simultaneously:

```bash
# Install multitail for enhanced experience
brew install multitail

# Then use the all-logs follow command
ichrisbirch testing app-logs-follow all
```

This will display all 5 service logs in a beautiful multi-pane view with color coding!

### Log Cleanup

```bash
# Remove the persistent log volume (clears all test logs)
docker volume rm ichrisbirch_testing_logs

# Or restart the test environment (will recreate empty logs)
ichrisbirch testing restart
```

## Benefits

1. **Post-Test Analysis**: Review logs after test stack is stopped
2. **Debugging**: Investigate intermittent test failures with full log history
3. **Performance Analysis**: Analyze service behavior over multiple test runs
4. **Separation**: Test logs are isolated from development/production logs
5. **Persistence**: Logs survive container restarts and stack recreation

## Log Format

All logs use the enhanced formatter with this structure:

```text
[LEVEL]   TIMESTAMP logger_name:function_name:line_number | message
```

Example:

```text
[INFO]    2025-01-20T15:30:45Z api.endpoints.habits:get_habits:45 | Retrieved 15 habits for user 123
[ERROR]   2025-01-20T15:30:46Z app.routes.habits:create_habit:89 | Failed to create habit: ValidationError
```

## Integration with Testing

### pytest Integration

When running tests, the persistent logs provide full context:

```bash
# Run tests
pytest tests/ichrisbirch/api/endpoints/test_habits.py -v

# Check logs for any issues
./scripts/view_test_logs.sh api -t 200
```

### Continuous Integration

In CI environments, logs can be extracted and archived:

```bash
# In CI pipeline after tests
docker run --rm -v ichrisbirch_testing_logs:/var/log/ichrisbirch -v $(pwd)/artifacts:/backup alpine:latest cp -r /var/log/ichrisbirch /backup/
```

## Troubleshooting

### Volume Not Found

```text
❌ Volume 'ichrisbirch_testing_logs' not found.
💡 Make sure the test environment has been started at least once:
   ichrisbirch testing start
```

### Permission Issues

If log files aren't created, check the log-init service:

```bash
docker-compose -f docker-compose.yml -f docker-compose.test.yml logs log-init
```

### Missing Logs

Ensure services are configured with proper environment variables and volume mounts in `docker-compose.test.yml`.
