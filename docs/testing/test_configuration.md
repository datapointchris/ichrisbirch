# Testing Configuration

Tests build their settings in code rather than reading a test `.env`. There is
one `.env` per environment, and the test suite does not use one.

## `test_settings` is the whole configuration

`get_test_runner_settings()` in `tests/utils/database.py` deep-copies the
process settings and overrides everything that points at a service:

```python
def get_test_runner_settings() -> Settings:
    test_settings = copy.deepcopy(get_settings())
    test_settings.ENVIRONMENT = 'testing'
    test_settings.protocol = 'http'
    test_settings.postgres.host = 'localhost'
    test_settings.postgres.port = 5434
    ...
    return test_settings


test_settings = get_test_runner_settings()
```

That module-level `test_settings` is what every fixture imports. `conftest.py`
passes it to `create_api`, to `DockerComposeTestEnvironment`, to
`truncate_all_tables` and to `create_session`, so one object decides what the
whole suite talks to.

The deep copy matters. The overrides mutate a `Settings` instance, and without
it they would reach back into the cached object `get_settings()` hands every
other caller in the process.

## Everything points at published ports on localhost

| Setting             | Value       |
| ------------------- | ----------- |
| `postgres.host`     | `localhost` |
| `postgres.port`     | 5434        |
| `sqlalchemy.port`   | 5434        |
| `fastapi.host`      | `localhost` |
| `fastapi.port`      | 8001        |
| `redis.port`        | 6380        |
| `protocol`          | `http`      |

pytest runs on the host, not in a container, so Docker DNS names like
`postgres` do not resolve for it. It reaches each service through the port that
`docker-compose.test.yml` publishes.

These numbers mirror that file and have to agree with it.
[Docker Compose Architecture](../docker/docker-compose.md#testing) carries the
published ports, and a disagreement between the two shows up as a connection
refused at session setup.

`protocol` is `http` because the suite talks to the API directly on 8001 rather
than through Traefik. Playwright's end-to-end tests are the exception: they go
through Traefik on 8443, over HTTPS, which is what makes a CORS or middleware
fault visible.

Postgres credentials are `postgres`/`postgres`. The test database is disposable
and its container publishes only to localhost.

## Running tests

```bash
./ops/icbops test run
./ops/icbops test run tests/ichrisbirch/api/endpoints/test_habits.py -v
```

`test run` exports `ENVIRONMENT=testing` and starts the containers if they are
down.

Running pytest by hand, leave `ENVIRONMENT` unset. `_detect_environment` returns
`testing` when pytest is in `sys.modules`, but an explicit `ENVIRONMENT` is
checked first and wins.

`test_settings` does not protect you from that. It sets `ENVIRONMENT` on its own
copy, and a test calling `get_settings()` directly gets the cached object
instead — which is whatever the shell said.

## What this buys

Anything reading `test_settings` does not depend on a `.env` that may or may not
be current, or on which environment was last brought up. The values are in
version control, next to the fixtures that use them.

It also means changing a test port is a two-file change:
`docker-compose.test.yml` publishes it and `get_test_runner_settings` connects
to it. A mismatch shows up as a connection refused at session setup rather than
as a failing assertion.

## Related

- [Test Environment](environment.md)
- [Fixtures](fixtures.md)
- [Configuration](../configuration.md)
