# LOG_DIR Configuration Guide

## Overview

The logging system now seamlessly handles log directory configuration across different environments using an environment variable approach with intelligent fallbacks.

## How It Works

### 1. Python Logger (ichrisbirch/logger.py)

The logger now uses a `get_log_base_location()` function with this priority order:

```python
def get_log_base_location():
    # 1. Check for explicit LOG_DIR environment variable (Docker/manual override)
    if log_dir := os.environ.get('LOG_DIR'):
        return log_dir

    # 2. Fall back to platform detection for bare metal deployments
    if platform.system() == 'Darwin':
        return '/usr/local/var/log/ichrisbirch'

    # 3. Default Linux location
    return '/var/log/ichrisbirch'
```

### 2. Docker Compose Configuration

All services now pass `LOG_DIR` as an environment variable to containers:

```yaml
environment:
  - LOG_DIR=${LOG_DIR:-/var/log/ichrisbirch}
```

Volume mounts use the same variable:

```yaml
volumes:
  - ${LOG_DIR:-/var/log/ichrisbirch}:/var/log/ichrisbirch
```

### 3. CLI Integration

The CLI already sets `LOG_DIR` based on platform:

```bash
if [[ $(uname) == "Darwin" ]]; then
    LOG_DIR="/usr/local/var/log/ichrisbirch"
else
    LOG_DIR="/var/log/ichrisbirch"
fi
```

## Environment Files

### Development (.dev.env.example)

```bash
# Development on macOS (host directory)
LOG_DIR=/usr/local/var/log/ichrisbirch
```

### Production (.prod.env.example)

```bash
# Production (standard Linux location)
LOG_DIR=/var/log/ichrisbirch
```

## Usage Scenarios

### 1. Development on macOS with Docker

```bash
# CLI automatically sets LOG_DIR=/usr/local/var/log/ichrisbirch
ichrisbirch dev start
# ✅ Logs go to /usr/local/var/log/ichrisbirch on host
# ✅ Python logger detects LOG_DIR env var and uses it
```

### 2. Production Linux with Docker

```bash
# CLI automatically sets LOG_DIR=/var/log/ichrisbirch
ichrisbirch prod start  
# ✅ Logs go to /var/log/ichrisbirch on host
# ✅ Python logger detects LOG_DIR env var and uses it
```

### 3. Bare Metal Development (no Docker)

```bash
# Python logger falls back to platform detection
# ✅ macOS: /usr/local/var/log/ichrisbirch
# ✅ Linux: /var/log/ichrisbirch
```

### 4. Custom Override

```bash
export LOG_DIR=/custom/log/path
ichrisbirch dev start
# ✅ Logs go to /custom/log/path
```

## Benefits

1. **Seamless**: No manual configuration needed
2. **Consistent**: Same log location on host and in container
3. **Flexible**: Easy to override for testing or custom deployments
4. **Backward Compatible**: Works with existing bare metal deployments
5. **Industry Standard**: Environment variable approach is widely used

## Migration

No migration needed! The new system:

- ✅ Automatically works with existing CLI usage
- ✅ Maintains platform detection for bare metal
- ✅ Adds Docker environment variable support
- ✅ Preserves all existing log file locations

Your existing setup will work unchanged, with improved Docker integration.
