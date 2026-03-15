"""Tests for npm dependencies collector schema and runner."""

from __future__ import annotations

import json
import tempfile
from datetime import UTC
from datetime import datetime
from pathlib import Path
from unittest.mock import patch


class TestNpmDependenciesSchema:
    """Tests for NpmDependenciesCollectEvent schema."""

    def test_npm_dependency_schema(self) -> None:
        """Test that NpmDependency captures all fields."""
        from stats.schemas.collectors.npm_dependencies import NpmDependency

        dep = NpmDependency(
            name='vue',
            version='3.4.0',
        )

        assert dep.name == 'vue'
        assert dep.version == '3.4.0'

    def test_npm_dependencies_collect_event_schema(self) -> None:
        """Test NpmDependenciesCollectEvent schema."""
        from stats.schemas.collectors.npm_dependencies import NpmDependenciesCollectEvent
        from stats.schemas.collectors.npm_dependencies import NpmDependency

        event = NpmDependenciesCollectEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            production_count=2,
            dev_count=1,
            total_count=3,
            production_dependencies=[
                NpmDependency(name='vue', version='3.4.0'),
                NpmDependency(name='pinia', version='2.1.7'),
            ],
            dev_dependencies=[
                NpmDependency(name='vitest', version='1.6.0'),
            ],
            duration_seconds=0.005,
        )

        assert event.type == 'collect.npm_dependencies'
        assert event.production_count == 2
        assert event.dev_count == 1
        assert event.total_count == 3
        assert len(event.production_dependencies) == 2
        assert len(event.dev_dependencies) == 1


class TestNpmDependenciesRunner:
    """Tests for npm dependencies collector runner."""

    def test_npm_runner_returns_none_for_missing_file(self) -> None:
        """Test runner returns None when package.json doesn't exist."""
        from stats.collectors.npm_dependencies import run

        with tempfile.TemporaryDirectory() as tmpdir:
            # Point __file__ to a location where frontend/package.json does not exist
            fake_file = Path(tmpdir) / 'stats' / 'collectors' / 'npm_dependencies.py'
            fake_file.parent.mkdir(parents=True)
            fake_file.touch()

            with patch('stats.collectors.npm_dependencies.__file__', str(fake_file)):
                event = run('master', 'ichrisbirch')

        assert event is None

    def test_npm_runner_parses_package_json(self) -> None:
        """Test runner correctly parses a package.json file."""
        from stats.collectors.npm_dependencies import run
        from stats.schemas.collectors.npm_dependencies import NpmDependenciesCollectEvent

        package_data = {
            'name': 'ichrisbirch-frontend',
            'dependencies': {
                'vue': '^3.4.0',
                'pinia': '~2.1.7',
                'axios': '1.6.0',
            },
            'devDependencies': {
                'vitest': '^1.6.0',
                'typescript': '~5.3.0',
            },
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            real_tmpdir = Path(tmpdir).resolve()

            # The runner does: Path(__file__).resolve().parent.parent.parent / 'frontend' / 'package.json'
            # With __file__ at <root>/stats/collectors/npm_dependencies.py, parent.parent.parent = <root>
            # So we create <root>/stats/collectors/npm_dependencies.py and <root>/frontend/package.json
            fake_file = real_tmpdir / 'stats' / 'collectors' / 'npm_dependencies.py'
            fake_file.parent.mkdir(parents=True)
            fake_file.touch()

            frontend_dir = real_tmpdir / 'frontend'
            frontend_dir.mkdir()
            package_json = frontend_dir / 'package.json'
            package_json.write_text(json.dumps(package_data))

            with patch('stats.collectors.npm_dependencies.__file__', str(fake_file)):
                event = run('master', 'ichrisbirch')

        assert event is not None
        assert isinstance(event, NpmDependenciesCollectEvent)
        assert event.production_count == 3
        assert event.dev_count == 2
        assert event.total_count == 5

        # Version prefixes (^ and ~) should be stripped
        vue_dep = next(d for d in event.production_dependencies if d.name == 'vue')
        assert vue_dep.version == '3.4.0'

        pinia_dep = next(d for d in event.production_dependencies if d.name == 'pinia')
        assert pinia_dep.version == '2.1.7'

        axios_dep = next(d for d in event.production_dependencies if d.name == 'axios')
        assert axios_dep.version == '1.6.0'
