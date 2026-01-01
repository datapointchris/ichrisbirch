"""Tests for radon collector."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from unittest.mock import MagicMock
from unittest.mock import patch


class TestRadonSchema:
    """Tests for RadonCollectEvent schema."""

    def test_function_complexity_schema(self) -> None:
        """Test FunctionComplexity captures all fields."""
        from stats.schemas.collectors.radon import FunctionComplexity

        func = FunctionComplexity(
            name='calculate_total',
            complexity=5,
            rank='A',
            lineno=42,
        )

        assert func.name == 'calculate_total'
        assert func.complexity == 5
        assert func.rank == 'A'
        assert func.lineno == 42

    def test_file_complexity_schema(self) -> None:
        """Test FileComplexity captures all fields."""
        from stats.schemas.collectors.radon import FileComplexity
        from stats.schemas.collectors.radon import FunctionComplexity

        file = FileComplexity(
            path='src/main.py',
            function_count=10,
            total_complexity=25,
            avg_complexity=2.5,
            max_complexity=8,
            maintainability_index=85.5,
            maintainability_rank='A',
            functions=[
                FunctionComplexity(name='main', complexity=3, rank='A', lineno=1),
            ],
        )

        assert file.path == 'src/main.py'
        assert file.function_count == 10
        assert file.avg_complexity == 2.5
        assert file.maintainability_index == 85.5

    def test_radon_collect_event_schema(self) -> None:
        """Test RadonCollectEvent schema."""
        from stats.schemas.collectors.radon import FileComplexity
        from stats.schemas.collectors.radon import RadonCollectEvent

        event = RadonCollectEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            files=[
                FileComplexity(
                    path='src/main.py',
                    function_count=10,
                    total_complexity=25,
                    avg_complexity=2.5,
                    max_complexity=8,
                    maintainability_index=85.5,
                    maintainability_rank='A',
                    functions=[],
                )
            ],
            total_files=1,
            avg_complexity=2.5,
            avg_maintainability=85.5,
            duration_seconds=0.5,
        )

        assert event.type == 'collect.radon'
        assert event.total_files == 1
        assert event.avg_complexity == 2.5


class TestRadonRunner:
    """Tests for radon collector runner."""

    def test_radon_runner_parses_output(self) -> None:
        """Test runner parses radon JSON output."""
        import tempfile
        from pathlib import Path

        from stats.collectors.radon import run
        from stats.schemas.collectors.radon import RadonCollectEvent

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test Python file
            test_file = Path(tmpdir) / 'test.py'
            test_file.write_text('def main():\n    pass\n')

            cc_output = f'{{"{test_file}": [{{"name": "main", "complexity": 1, "rank": "A", "lineno": 1}}]}}'
            mi_output = f'{{"{test_file}": {{"mi": 100.0, "rank": "A"}}}}'

            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = [
                    MagicMock(returncode=0, stdout=cc_output),
                    MagicMock(returncode=0, stdout=mi_output),
                ]

                event = run('master', 'ichrisbirch', tmpdir)

                assert event is not None
                assert isinstance(event, RadonCollectEvent)
                assert event.total_files == 1
                assert event.files[0].maintainability_index == 100.0

    def test_radon_runner_returns_none_for_no_python_files(self) -> None:
        """Test runner returns None when no Python files found."""
        import tempfile

        from stats.collectors.radon import run

        with tempfile.TemporaryDirectory() as tmpdir:
            # Empty directory with no Python files
            event = run('master', 'ichrisbirch', tmpdir)

            assert event is None
