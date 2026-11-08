# Testing Configuration

Tests are configured from `tests/testing.env`, which is committed because
every value in it was made for the tests. Importing the `tests` package loads
it, so it reaches every pytest run before any fixture reads a setting. The test
stack's compose file passes the same file to each app container. Under
`testing`, `get_settings()` reads only the process environment and never a
checkout's `.env`, which on a workstation is the development one. The process
environment overrides any value in the file.

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

`PrivateServices` in `tests/environment.py` writes this session's Postgres and
Redis into `test_settings`. Each is the server `TEST_DATABASE_URL` or
`TEST_REDIS_URL` names, where the environment provides one. Otherwise the
session starts its own container, and the values are where Docker published it:

| Setting                            | Value                                                 |
| ---------------------------------- | ----------------------------------------------------- |
| `postgres.host`, `sqlalchemy.host` | the URL's host, or the container host Docker reports  |
| `postgres.port`, `sqlalchemy.port` | the URL's port, or the port Docker picked for 5432    |
| `postgres.username`, `.password`   | the URL's, or `postgres` / `postgres`                 |
| `redis.host`, `redis.port`         | the same, for 6379                                    |
| `redis.password`                   | the URL's, or none                                    |
| `redis.db`                         | the URL's, or `REDIS_DB` from `tests/testing.env`     |

A container's port is never fixed, so no two sessions collide and nothing has
to agree with a compose file. Nothing builds an engine or a Redis client at import time, so
writing the settings in the session fixture reaches every later connection.

`protocol` is `http` because the suite calls the API in-process through
FastAPI's `TestClient` rather than through Traefik. Playwright's end-to-end
tests are the exception: they go through the test stack's Traefik, over HTTPS,
which is what makes a CORS or middleware fault visible.
[Test Environment](environment.md) covers both.

## Running tests

```bash
./ops/lifeops test run
./ops/lifeops test run tests/life/api/endpoints/test_habits.py -v
```

`test run` exports `ENVIRONMENT=testing` and writes its reports to
`.test-reports/`.

Running pytest by hand, leave `ENVIRONMENT` unset. `detect_environment` returns
`testing` when pytest is in `sys.modules`, but an explicit `ENVIRONMENT` is
checked first and wins.

`test_settings` does not protect you from that. It sets `ENVIRONMENT` on its own
copy. A test calling `get_settings()` directly gets the cached object instead,
which carries whatever the shell said.

## The values are in version control, not in a checkout's `.env`

A test run does not depend on a `.env` that may or may not be current, or on
which environment was last brought up. Its values sit next to the fixtures that
use them, and the services they point at exist only for the session. The e2e
stack reads the same file, as its containers' `env_file` and as the compose
project's interpolation source.

## Related

- [Test Environment](environment.md)
- [Fixtures](fixtures.md)
- [Configuration](../configuration.md)
