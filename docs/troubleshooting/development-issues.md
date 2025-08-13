# Development Environment Troubleshooting

This document covers issues related to setting up and maintaining the development environment for the iChrisBirch project.

## Initial Setup Issues

### Python Version Compatibility

**Problem:** Wrong Python version installed or being used.

**Symptoms:**

- `Python version not supported` errors
- Package installation failures
- Syntax errors with modern Python features

**Resolution:**

1. **Verify Python version:**

```bash
python --version  # Should be 3.12.x
which python      # Verify correct Python binary
```

1. **Install correct Python version:**

```bash
# macOS with Homebrew
brew install python@3.12

# Ubuntu/Debian
sudo apt update
sudo apt install python3.12 python3.12-venv

# Using pyenv (recommended)
pyenv install 3.12.0
pyenv local 3.12.0
```

### UV Package Manager Setup

**Problem:** UV not installed or not working correctly.

**Installation:**

```bash
# Install UV
pip install uv

# Verify installation
uv --version

# Update UV
pip install --upgrade uv
```

**Common UV Issues:**

1. **Cache corruption:**

```bash
# Clear UV cache
uv cache clean

# Reinstall dependencies
rm uv.lock
uv sync
```

1. **Virtual environment issues:**

```bash
# Recreate virtual environment
rm -rf .venv
uv sync
```

### Docker Setup Problems

**Problem:** Docker not installed or not working properly.

**Basic Docker Setup:**

```bash
# Verify Docker installation
docker --version
docker-compose --version

# Test Docker functionality
docker run hello-world

# Check Docker daemon status
docker info
```

**Common Docker Issues:**

1. **Permission issues on Linux:**

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, or restart
```

1. **Docker daemon not running:**

```bash
# Start Docker service (Linux)
sudo systemctl start docker
sudo systemctl enable docker

# macOS - Start Docker Desktop application
```

## Environment Configuration Issues

### Environment Variables Not Loading

**Problem:** Application can't find required environment variables.

**Diagnosis:**

```bash
# Check if environment file exists
ls -la .env*

# Verify environment variables are loaded
docker-compose exec app env | grep -i postgres
```

**Resolution:**

1. **Create environment files:**

```bash
# Copy example files
cp .env.example .env
cp .env.test.example .env.test

# Edit with your values
vim .env
```

1. **Verify Docker Compose loads environment:**

```yaml
# docker-compose.yml
services:
  app:
    env_file:
      - .env
    environment:
      - NODE_ENV=development
```

### Configuration Conflicts

**Problem:** Different configuration values between environments.

**Common Issues:**

1. **Database URL mismatches**
1. **API endpoint differences**
1. **Debug settings conflicts**

**Resolution:**

Create environment-specific configuration:

```python
# ichrisbirch/config.py
import os
from typing import Literal

class Settings:
    def __init__(self):
        self.environment: Literal["development", "testing", "production"] = \
            os.environ["ENVIRONMENT"]

        # Environment-specific settings
        if self.environment == "testing":
            self.database_url = os.environ["TEST_DATABASE_URL"]
            self.debug = True
        elif self.environment == "production":
            self.database_url = os.environ["PROD_DATABASE_URL"]
            self.debug = False
        else:  # development
            self.database_url = os.environ["DEV_DATABASE_URL"]
            self.debug = True

settings = Settings()
```

## IDE and Editor Issues

### VS Code Extension Problems

**Problem:** Python extension not working or missing features.

**Resolution:**

1. **Install required extensions:**

```bash
code --install-extension ms-python.python
code --install-extension ms-python.pylint
code --install-extension ms-python.black-formatter
```

1. **Configure Python interpreter:**

```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black"
}
```

### Import Resolution Issues

**Problem:** IDE can't find imports or shows false errors.

**Common Causes:**

1. **Wrong Python interpreter selected**
1. **Package not installed in editable mode**
1. **Missing `__init__.py` files**

**Resolution:**

```bash
# Install package in editable mode
uv sync

# Verify package is installed
uv run python -c "import ichrisbirch; print(ichrisbirch.__file__)"

# Check Python path
uv run python -c "import sys; print('\n'.join(sys.path))"
```

## Development Workflow Issues

### Git Configuration Problems

**Problem:** Git not configured or authentication issues.

**Setup:**

```bash
# Configure Git
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Configure SSH key for GitHub
ssh-keygen -t ed25519 -C "your.email@example.com"
cat ~/.ssh/id_ed25519.pub  # Add to GitHub

# Test SSH connection
ssh -T git@github.com
```

### Pre-commit Hook Issues

**Problem:** Pre-commit hooks fail or don't run.

**Setup:**

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files

# Skip hooks if needed (emergency only)
git commit --no-verify
```

### Code Formatting Conflicts

**Problem:** Different formatting tools producing conflicting results.

**Resolution:**

Create consistent configuration:

```toml
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py312']

[tool.isort]
profile = "black"
line_length = 88

[tool.pylint.messages_control]
max-line-length = 88
```

## Performance and Resource Issues

### Slow Development Environment

**Problem:** Local development is slow or unresponsive.

**Common Causes:**

1. **Insufficient resources for Docker**
1. **Too many services running**
1. **Large log files**

**Resolution:**

1. **Optimize Docker resources:**

```yaml
# docker-compose.yml - limit resource usage
services:
  app:
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

1. **Selective service startup:**

```bash
# Start only essential services
docker-compose up app postgres

# Start additional services as needed
docker-compose up redis nginx
```

1. **Clean up logs:**

```bash
# Rotate log files
docker-compose logs --no-color > logs/app.log
docker-compose down
docker system prune -f
```

### Port Conflicts

**Problem:** Ports already in use by other applications.

**Diagnosis:**

```bash
# Check what's using specific port
lsof -i :8000
netstat -tulpn | grep :8000

# Kill process using port
kill -9 $(lsof -t -i:8000)
```

**Resolution:**

1. **Change ports in docker-compose:**

```yaml
services:
  app:
    ports:
      - "8001:8000"  # Use different external port
```

1. **Use different ports for different projects:**

```bash
# Project-specific environment variables
echo "APP_PORT=8001" >> .env
echo "POSTGRES_PORT=5433" >> .env
```

## Debugging and Troubleshooting Tools

### Development Debugging

**Enable Debug Mode:**

```python
# In your application
import logging

# Set up debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add debug prints
logger.debug(f"Settings loaded: {settings}")
logger.debug(f"Database URL: {settings.database_url}")
```

### Container Debugging

**Access container shell:**

```bash
# Get shell in running container
docker-compose exec app bash

# Run container with override
docker-compose run --rm app bash

# Debug specific service
docker-compose run --rm --entrypoint="" app bash
```

### Network Debugging

**Test service connectivity:**

```bash
# Test from host to container
curl http://localhost:8000/health

# Test container to container
docker-compose exec app curl http://api:8000/health

# Check DNS resolution
docker-compose exec app nslookup postgres
```

## Environment Validation Script

Create a validation script to check environment setup:

```python
#!/usr/bin/env python3
# scripts/validate_dev_env.py
"""
Development environment validation script.
Run this to verify your development setup is correct.
"""

import sys
import subprocess
import os
from pathlib import Path

def check_command(command: str, name: str) -> bool:
    """Check if a command is available."""
    try:
        result = subprocess.run(
            [command, "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✓ {name}: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass

    print(f"✗ {name}: Not found")
    return False

def check_file(filepath: str, name: str) -> bool:
    """Check if a file exists."""
    if Path(filepath).exists():
        print(f"✓ {name}: Found")
        return True
    else:
        print(f"✗ {name}: Missing")
        return False

def check_docker_compose() -> bool:
    """Check if Docker Compose services can start."""
    try:
        result = subprocess.run(
            ["docker-compose", "config"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓ Docker Compose: Configuration valid")
            return True
        else:
            print(f"✗ Docker Compose: Configuration error\n{result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Docker Compose: {e}")
        return False

def main():
    """Run all validation checks."""
    print("🔍 Validating development environment...\n")

    checks = [
        # Core tools
        (lambda: check_command("python3", "Python"), "Python 3"),
        (lambda: check_command("uv", "UV Package Manager"), "UV"),
        (lambda: check_command("docker", "Docker"), "Docker"),
        (lambda: check_command("docker-compose", "Docker Compose"), "Docker Compose"),
        (lambda: check_command("git", "Git"), "Git"),

        # Configuration files
        (lambda: check_file(".env", ".env file"), "Environment file"),
        (lambda: check_file("pyproject.toml", "pyproject.toml"), "Project config"),
        (lambda: check_file("docker-compose.yml", "docker-compose.yml"), "Docker Compose config"),

        # Docker validation
        (check_docker_compose, "Docker Compose validation"),
    ]

    passed = 0
    total = len(checks)

    for check_func, name in checks:
        if check_func():
            passed += 1
        print()

    # Summary
    print(f"📊 Validation Summary: {passed}/{total} checks passed")

    if passed == total:
        print("🎉 Development environment is ready!")
        return 0
    else:
        print("❌ Some issues need to be resolved before development")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

Run the validation script:

```bash
# Make executable
chmod +x scripts/validate_dev_env.py

# Run validation
./scripts/validate_dev_env.py
```

## Quick Setup Guide

For new developers, here's a quick setup checklist:

```bash
# 1. Clone repository
git clone https://github.com/username/ichrisbirch.git
cd ichrisbirch

# 2. Copy environment files
cp .env.example .env
cp .env.test.example .env.test

# 3. Install UV
pip install uv

# 4. Install dependencies
uv sync

# 5. Start development environment
docker-compose up -d

# 6. Run validation
./scripts/validate_dev_env.py

# 7. Run tests to verify setup
docker-compose -f docker-compose.test.yml up test-runner
```

## Common Development Commands

Keep these handy for daily development:

```bash
# Start development environment
docker-compose up -d

# View logs
docker-compose logs -f app

# Run tests
docker-compose -f docker-compose.test.yml up test-runner

# Access application shell
docker-compose exec app bash

# Install new package
uv add package-name

# Run database migrations
docker-compose exec app uv run alembic upgrade head

# Format code
uv run black ichrisbirch/
uv run isort ichrisbirch/

# Lint code
uv run pylint ichrisbirch/

# Stop all services
docker-compose down

# Clean up Docker resources
docker system prune -f
docker-compose down -v  # Remove volumes too
```
