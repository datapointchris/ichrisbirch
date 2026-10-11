"""Tests for collector discovery mechanism."""

from __future__ import annotations

from stats.collectors import discover_collectors
from stats.collectors import get_collector


class TestCollectorDiscovery:
    """Tests for collector discovery."""

    def test_discover_collectors_finds_all_collectors(self) -> None:
        """Test that discover_collectors finds all implemented collectors."""
        collectors = discover_collectors()

        expected_collectors = {
            'tokei',
            'pytest_collector',
            'coverage',
            'docker',
            'dependencies',
            'files',
        }
        assert expected_collectors.issubset(set(collectors.keys()))

    def test_discovered_collectors_are_callable(self) -> None:
        """Test that discovered collectors are callable."""
        collectors = discover_collectors()

        for name, collector_fn in collectors.items():
            assert callable(collector_fn), f'{name} collector is not callable'

    def test_get_collector_returns_collector(self) -> None:
        """Test that get_collector returns a collector by name."""
        tokei_collector = get_collector('tokei')
        assert tokei_collector is not None
        assert callable(tokei_collector)

    def test_get_collector_returns_none_for_unknown(self) -> None:
        """Test that get_collector returns None for unknown collectors."""
        unknown_collector = get_collector('nonexistent_collector')
        assert unknown_collector is None
