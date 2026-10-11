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

Each pytest session starts its own Postgres and Redis and removes them when it
ends, so nothing needs starting first. The e2e suite is
`./ops/icbops test e2e`, which starts this checkout's test stack if it is down.
[Test Environment](environment.md) covers both.

`test run` exports `ENVIRONMENT=testing` itself, so nothing is needed from the
shell.

Running pytest by hand, leave `ENVIRONMENT` unset. `detect_environment` in
`ichrisbirch/config.py` returns `testing` when pytest is in `sys.modules`. An
`ENVIRONMENT` already exported in your shell outranks that check, and every
test calling `get_settings()` directly then gets that environment's settings.

`test_settings` is not a defense against this. It sets `ENVIRONMENT` on the copy
it builds, never on the cached object `get_settings()` returns.
[Testing Configuration](test_configuration.md) covers what it does override.

### Local DNS

Traefik routes by host name, so a browser needs the names resolving. pytest
does not, because it calls the API in-process.

The `*.test.localhost` names need no host entry. The e2e suite resolves them
inside the test stack, through Docker's DNS and a Chromium resolver rule. Only
the dev stack's `*.docker.localhost` names, listed in
[Quick Start](../quick-start.md), belong in `/etc/hosts`. Those are what a
browser and `E2E_ENV=dev` need.

```bash
grep -E 'docker\.localhost' /etc/hosts
```

### `pytest-xdist`

It is not installed. Under it, each worker would run the session fixture and
start its own Postgres and Redis, so workers would never share a database.
