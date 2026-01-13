# CI/CD Pipeline

This document details the Continuous Integration and Continuous Deployment workflows for the ichrisbirch project.

## Overview

The project uses GitHub Actions for CI/CD with the following workflows:

| Workflow | File | Trigger | Purpose |
|----------|------|---------|---------|
| Validate Project | `validate-project.yml` | Push to master, PRs | Run linting, type checking, and tests |
| Deploy MkDocs | `deploy-docs.yml` | Push to master (docs changes) | Build and deploy documentation |
| Sync Documentation Code | `sync-docs.yml` | Push to master | Sync code snippets in documentation |

## Validate Project Workflow

The main CI workflow that validates code quality and runs tests.

### Workflow Stages

```text
1. Checkout & Setup
   ├── Checkout repository
   ├── Set up Python 3.13
   ├── Install UV package manager
   └── Install dependencies (uv sync)

2. Code Quality
   ├── Ruff linting
   ├── Ruff formatting check
   └── MyPy type checking

3. Docker Environment Setup
   ├── Set up Docker Compose
   ├── Configure AWS credentials (OIDC)
   ├── Create test-logs directory
   ├── Create Docker network (proxy)
   └── Start Docker Compose containers

4. Test Execution
   ├── Run pytest with coverage
   └── Generate coverage reports

5. Cleanup
   └── Stop Docker Compose containers
```

### Docker Compose in CI

The CI environment uses a special Docker Compose configuration that differs from local development:

```bash
docker compose -f docker-compose.yml -f docker-compose.test.yml -f docker-compose.ci.yml \
  --project-name ichrisbirch-test up -d
```

**Three compose files are layered:**

1. `docker-compose.yml` - Base production configuration
2. `docker-compose.test.yml` - Test-specific overrides (different ports, tmpfs for speed)
3. `docker-compose.ci.yml` - CI-specific overrides (removes local bind mounts)

### CI-Specific Configuration (`docker-compose.ci.yml`)

The CI override file addresses differences between local and CI environments:

| Issue | Local Development | CI Environment | CI Override Solution |
|-------|-------------------|----------------|---------------------|
| AWS credentials | `~/.config/aws` mounted | Environment variables via OIDC | Remove bind mount |
| Docker network | External `proxy` network | Network doesn't exist | Create as bridge network |
| File mounts | Local paths exist | Only repo checkout | Use volumes only |
| Traefik dashboard | Enabled with auth | Not needed | Disabled |

### Container Startup Sequence

The workflow starts containers in a specific order to handle dependencies:

```bash
# Phase 1: Start database services first
docker compose ... up -d --build postgres redis
sleep 10  # Wait for health checks

# Phase 2: Start application services
docker compose ... up -d --build api app chat scheduler
sleep 30  # Wait for services to initialize
```

**Why this order matters:**

- `postgres` and `redis` must be healthy before application services start
- `api` initializes the shared virtual environment used by other services
- `scheduler` creates the `apscheduler_jobs` table needed by scheduler tests
- Sleep intervals allow health checks to complete

### Test Environment Detection

The test fixtures detect CI environment and adjust behavior:

```python
# In tests/environment.py
@property
def is_ci(self) -> bool:
    return os.environ.get('CI', '').lower() == 'true'
```

**CI-specific behavior:**

- Skip Docker Compose startup (containers pre-started by workflow)
- Skip Docker Compose teardown (handled by workflow cleanup step)
- Longer wait times for container health checks

### Environment Variables

Key environment variables set in CI:

```yaml
env:
  ENVIRONMENT: testing
  CI: true  # Detected by test fixtures
  AWS_REGION: us-east-2
  # AWS credentials via OIDC (not stored as secrets)
```

### AWS Authentication

The workflow uses OIDC (OpenID Connect) for AWS authentication instead of long-lived credentials:

```yaml
- name: Configure AWS Credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::${{ vars.AWS_ACCOUNT_ID }}:role/github-actions-${{ github.event.repository.name }}-role
    aws-region: ${{ vars.AWS_REGION }}
```

This provides temporary credentials that expire after the workflow completes.

## Deploy MkDocs Workflow

Builds and deploys documentation to GitHub Pages.

### Trigger Conditions

```yaml
on:
  push:
    branches: [main]
    paths:
      - 'docs/**'
      - 'mkdocs.yml'
      - 'tools/docs/**'
```

### Custom MkDocs Plugins

The project uses custom MkDocs plugins that must be installed:

- `code_sync` - Synchronizes code snippets in documentation
- `diagrams` - Generates architecture diagrams

These are registered as entry points in `pyproject.toml`:

```toml
[project.entry-points."mkdocs.plugins"]
code_sync = "tools.docs.mkdocs_code_sync_plugin:CodeSyncPlugin"
diagrams = "tools.docs.mkdocs_diagrams_plugin:DiagramGeneratorPlugin"
```

The workflow uses `uv sync` to install all dependencies including these plugins.

## Troubleshooting CI Failures

### Common Issues

#### 1. Docker Compose containers not starting

```yaml
Error: Failed to start Docker Compose test environment
```

Check:

- Docker Compose CI override file exists
- Proxy network creation step succeeded
- Container health checks are passing

#### 2. Missing database table

```yaml
Error: relation "apscheduler_jobs" does not exist
```

Ensure scheduler container is started:

```yaml
docker compose ... up -d --build api app chat scheduler
```

#### 3. MkDocs plugin not found

```yaml
Error: The "code_sync" plugin is not installed
```

Ensure workflow uses `uv sync` instead of just `pip install mkdocs-material`.

#### 4. AWS credential issues

```yaml
Error: Unable to locate credentials
```

Check:

- OIDC role is configured correctly in AWS
- Repository variables `AWS_ACCOUNT_ID` and `AWS_REGION` are set
- IAM role trust policy allows the repository

### Viewing CI Logs

Use the tracking script to view workflow logs:

```bash
# List recent runs
./scripts/track-gh-actions-workflow.sh list

# Watch a running workflow
./scripts/track-gh-actions-workflow.sh watch

# Get failure logs
./scripts/track-gh-actions-workflow.sh logs
```

Or use the GitHub CLI directly:

```bash
# List runs
gh run list

# View specific run
gh run view <run-id>

# Get failed job logs
gh run view <run-id> --log-failed
```

## Local Testing Before Push

To catch CI issues before pushing:

```bash
# Run linting
uv run ruff check .
uv run ruff format --check .

# Run type checking
uv run mypy ichrisbirch/

# Run tests with the same configuration as CI
./cli/ichrisbirch testing start
uv run pytest --cov=ichrisbirch
./cli/ichrisbirch testing stop
```

## Workflow Files Reference

| File | Purpose |
|------|---------|
| `.github/workflows/validate-project.yml` | Main CI workflow |
| `.github/workflows/deploy-docs.yml` | Documentation deployment |
| `.github/workflows/sync-docs.yml` | Code sync in docs |
| `docker-compose.ci.yml` | CI-specific Docker Compose overrides |
| `tests/environment.py` | Test environment with CI detection |
