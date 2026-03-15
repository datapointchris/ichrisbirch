"""Tests for dependencies collector schema and runner."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from unittest.mock import MagicMock
from unittest.mock import patch


class TestDependenciesSchema:
    """Tests for DependenciesCollectEvent schema."""

    def test_dependency_schema(self) -> None:
        """Test Dependency captures all fields."""
        from stats.schemas.collectors.dependencies import Dependency

        dep = Dependency(name='pydantic', version='2.0.0')

        assert dep.name == 'pydantic'
        assert dep.version == '2.0.0'

    def test_dependencies_collect_event_schema(self) -> None:
        """Test DependenciesCollectEvent schema."""
        from stats.schemas.collectors.dependencies import DependenciesCollectEvent
        from stats.schemas.collectors.dependencies import Dependency

        event = DependenciesCollectEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            dependencies=[Dependency(name='pydantic', version='2.0.0')],
            total_count=1,
            duration_seconds=0.5,
        )

        assert event.type == 'collect.dependencies'
        assert event.total_count == 1


class TestDependenciesRunner:
    """Tests for dependencies collector runner."""

    def test_dependencies_runner_parses_output(self) -> None:
        """Test runner parses uv pip list output."""
        from stats.collectors.dependencies import run
        from stats.schemas.collectors.dependencies import DependenciesCollectEvent

        mock_output = 'pydantic==2.0.0\nfastapi==0.100.0\n'

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output,
                stderr='',
            )

            event = run('master', 'ichrisbirch')

            assert isinstance(event, DependenciesCollectEvent)
            assert event.total_count == 2
            assert event.dependencies[0].name == 'pydantic'
