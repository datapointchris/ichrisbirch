"""Tests for config loading."""

from __future__ import annotations

from stats.config import load_config


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_reads_pyproject(self) -> None:
        config = load_config()

        # Should have project name from [tool.devstats]
        assert 'project' in config

    def test_load_config_has_default_hooks(self) -> None:
        config = load_config()

        hooks = config.get('capture', {}).get('hooks', [])
        # Default hooks should include ruff_check and mypy
        assert 'ruff_check' in hooks
        assert 'mypy' in hooks

    def test_load_config_has_events_path(self) -> None:
        config = load_config()

        assert 'events_path' in config
        assert 'events.jsonl' in config['events_path']

    def test_load_config_has_collectors(self) -> None:
        config = load_config()

        collectors = config.get('collect', {}).get('collectors', [])
        assert 'tokei' in collectors
