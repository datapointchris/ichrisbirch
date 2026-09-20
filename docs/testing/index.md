# Testing

Start at the overview; the other pages go one layer deeper on a single part of the infrastructure.

## Documentation

- [Testing Overview](overview.md) — the layered architecture, and the map across every other testing page
- [Testing Guide](testing.md) — running pytest by hand, the `ENVIRONMENT` variable, and `/etc/hosts` on Mac
- [Test Environment](environment.md) — the Docker Compose containers, their ports, and how their lifecycle is driven
- [Test Configuration](test_configuration.md) — the hardcoded settings in `tests/utils/test_settings.py`
- [Test Fixtures](fixtures.md) — every fixture by scope, what it sets up, and which conftest defines it
- [Test Data](test_data.md) — the `tests.test_data` package, `BASE_DATA`, and model instantiation
- [Writing Tests](writing_tests.md) — where a test file goes, how it is named, and the types of test in use
- [Persistent Logging](persistent-logging.md) — reading test container logs through the CLI across restarts
- [Visualization Options](visualization_options.md) — alternatives to Mermaid weighed for diagrams in these docs
