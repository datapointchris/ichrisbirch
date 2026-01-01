"""Tests for config loading."""

from __future__ import annotations


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_reads_pyproject(self) -> None:
        from stats.config import load_config

        config = load_config()

        # Should have project name from [tool.devstats]
        assert 'project' in config

    def test_load_config_has_default_hooks(self) -> None:
        from stats.config import load_config

        config = load_config()

        hooks = config.get('capture', {}).get('hooks', [])
        # Default hooks should include ruff and mypy
        assert 'ruff' in hooks
        assert 'mypy' in hooks

    def test_load_config_has_events_path(self) -> None:
        from stats.config import load_config

        config = load_config()

        assert 'events_path' in config
        assert 'events.jsonl' in config['events_path']

    def test_load_config_has_collectors(self) -> None:
        from stats.config import load_config

        config = load_config()

        collectors = config.get('collect', {}).get('collectors', [])
        assert 'tokei' in collectors
