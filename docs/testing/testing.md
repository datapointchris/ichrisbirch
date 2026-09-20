# Testing Guide

This document provides a high-level overview of the testing system in the ichrisbirch project. For more detailed information, please refer to the specific documentation files linked below.

## Comprehensive Testing Documentation

We now have detailed documentation for the testing infrastructure:

1. [Testing Overview](overview.md) - The big picture of the testing infrastructure
2. [Test Fixtures](fixtures.md) - Documentation of available test fixtures and their usage
3. [Test Data Management](test_data.md) - How test data is organized and managed
4. [Test Environment Configuration](environment.md) - Details of the test environment setup
5. [Writing Tests](writing_tests.md) - Guide to writing effective tests

## Running Tests

```bash
./ops/icbops test run
./ops/icbops test run tests/ichrisbirch/api/endpoints/test_habits.py -v
```

`test run` starts the test containers if they are down and waits for their
health checks, so no manual start is needed first.

`ENVIRONMENT` does not need setting. `test_settings` in
`tests/utils/database.py` sets it to `testing` on a copy of the process
settings, so whatever the shell holds is irrelevant.
[Testing Configuration](test_configuration.md) covers the rest of what it
overrides.

### Local DNS

Traefik routes by host name, so the browser and Playwright need these
resolving:

```bash
grep docker.localhost /etc/hosts
```

[Quick Start](../quick-start.md) has the entries to add. pytest itself does not
need them — it reaches the API on a published port rather than through Traefik.

### `pytest-xdist`

Do not add it. The session fixture starts the Docker Compose stack once, and
xdist would run that startup per worker against one set of ports.
