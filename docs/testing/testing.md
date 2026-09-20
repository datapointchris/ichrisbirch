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

`test run` exports `ENVIRONMENT=testing` itself, so nothing is needed from the
shell.

Running pytest by hand, leave `ENVIRONMENT` unset. `_detect_environment` in
`ichrisbirch/config.py` returns `testing` when pytest is in `sys.modules`. An
`ENVIRONMENT` already exported in your shell outranks that check, and every
test calling `get_settings()` directly then gets that environment's settings.

`test_settings` is not a defense against this. It sets `ENVIRONMENT` on the copy
it builds, never on the cached object `get_settings()` returns.
[Testing Configuration](test_configuration.md) covers what it does override.

### Local DNS

Traefik routes by host name, so Playwright and the browser need the names
resolving. pytest does not. It reaches the API on a published port rather than
through Traefik.

```bash
grep -E 'docker\.localhost|test\.localhost' /etc/hosts
```

Playwright targets `*.test.localhost` by default, listed in
[Traefik deployment](../traefik-deployment.md).
[Quick Start](../quick-start.md) lists the `*.docker.localhost` entries, which
are what `E2E_ENV=dev` needs.

### `pytest-xdist`

Do not add it. The session fixture starts the Docker Compose stack once. xdist
would run that startup once per worker, against one set of ports.
