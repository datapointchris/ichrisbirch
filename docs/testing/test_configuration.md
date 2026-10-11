# Testing Configuration

Tests build their settings in code rather than reading a test `.env`. There is
one `.env` per environment, and the test suite does not use one.

## `test_settings` is the whole configuration

`build_session_settings()` in `tests/utils/database.py` deep-copies the process
settings and marks them as the test environment:

```python
def build_session_settings() -> Settings:
    settings = copy.deepcopy(get_settings())
    settings.ENVIRONMENT = 'testing'
    settings.protocol = 'http'
    return settings


test_settings = build_session_settings()
```

That module-level `test_settings` is what every fixture imports. `conftest.py`
passes it to `create_api`, to `PrivateServices`, to `truncate_all_tables` and to
`create_session`. One object decides what the whole suite talks to.

The overrides mutate a `Settings` instance in place. Without the deep copy they
would reach back into the cached object `get_settings()` hands every other
caller in the process. `get_test_runner_settings()` returns a further copy for a
test that changes a setting, so the change reaches no other test.

## The session's services decide the hosts and ports

`PrivateServices` in `tests/environment.py` starts this session's Postgres and
Redis, then writes where Docker published them into `test_settings`:

| Setting                            | Value                             |
| ---------------------------------- | --------------------------------- |
| `postgres.host`, `sqlalchemy.host` | the container host Docker reports |
| `postgres.port`, `sqlalchemy.port` | the port Docker picked for 5432   |
| `postgres.username`, `.password`   | `postgres` / `postgres`           |
| `redis.host`, `redis.port`         | the same, for 6379                |
| `redis.password`                   | empty                             |

No port is fixed, so no two sessions collide and nothing has to agree with a
compose file. Nothing builds an engine or a Redis client at import time, so
writing the settings in the session fixture reaches every later connection.

`protocol` is `http` because the suite calls the API in-process through
FastAPI's `TestClient` rather than through Traefik. Playwright's end-to-end
tests are the exception: they go through the test stack's Traefik, over HTTPS,
which is what makes a CORS or middleware fault visible.
[Test Environment](environment.md) covers both.

## Running tests

```bash
./ops/icbops test run
./ops/icbops test run tests/ichrisbirch/api/endpoints/test_habits.py -v
```

`test run` exports `ENVIRONMENT=testing` and writes its reports to
`.test-reports/`.

Running pytest by hand, leave `ENVIRONMENT` unset. `detect_environment` returns
`testing` when pytest is in `sys.modules`, but an explicit `ENVIRONMENT` is
checked first and wins.

`test_settings` does not protect you from that. It sets `ENVIRONMENT` on its own
copy. A test calling `get_settings()` directly gets the cached object instead,
which carries whatever the shell said.

## The values are in version control, not in a `.env`

Anything reading `test_settings` does not depend on a `.env` that may or may not
be current, or on which environment was last brought up. The values sit next to
the fixtures that use them, and the services they point at exist only for the
session.

## Related

- [Test Environment](environment.md)
- [Fixtures](fixtures.md)
- [Configuration](../configuration.md)
