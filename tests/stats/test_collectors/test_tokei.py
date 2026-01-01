"""Tests for tokei collector schema and runner."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'tool_outputs'


class TestTokeiSchema:
    """Tests for TokeiCollectEvent schema."""

    def test_tokei_language_stats_schema(self) -> None:
        """Test that TokeiLanguageStats captures all fields."""
        from stats.schemas.collectors.tokei import TokeiFile
        from stats.schemas.collectors.tokei import TokeiFileStats
        from stats.schemas.collectors.tokei import TokeiLanguageStats

        stats = TokeiLanguageStats(
            blanks=100,
            code=1000,
            comments=50,
            files=[
                TokeiFile(
                    name='test.py',
                    stats=TokeiFileStats(blanks=10, code=100, comments=5),
                )
            ],
            inaccurate=False,
        )

        assert stats.code == 1000
        assert len(stats.files) == 1
        assert stats.files[0].name == 'test.py'

    def test_tokei_collect_event_schema(self) -> None:
        """Test TokeiCollectEvent schema."""
        from stats.schemas.collectors.tokei import TokeiCollectEvent
        from stats.schemas.collectors.tokei import TokeiLanguageStats

        event = TokeiCollectEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            languages={'Python': TokeiLanguageStats(blanks=100, code=1000, comments=50, files=[])},
            total_code=1000,
            total_comments=50,
            total_blanks=100,
            total_files=10,
            duration_seconds=0.5,
        )

        assert event.type == 'collect.tokei'
        assert 'Python' in event.languages
        assert event.total_code == 1000


class TestTokeiRunner:
    """Tests for tokei collector runner."""

    def test_tokei_runner_returns_typed_event(self) -> None:
        """Test runner returns TokeiCollectEvent."""
        from stats.collectors.tokei import run
        from stats.schemas.collectors.tokei import TokeiCollectEvent

        sample_output = (FIXTURES_DIR / 'tokei_sample.json').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=sample_output,
                stderr='',
            )

            event = run('master', 'ichrisbirch')

            assert isinstance(event, TokeiCollectEvent)
            assert 'Python' in event.languages
            assert event.languages['Python'].code == 8789

    def test_tokei_runner_calculates_totals(self) -> None:
        """Test runner calculates totals correctly."""
        from stats.collectors.tokei import run

        sample_output = (FIXTURES_DIR / 'tokei_sample.json').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=sample_output,
                stderr='',
            )

            event = run('master', 'ichrisbirch')

            # Sum of Python (8789) + JS (296) + HTML (2752) + CSS (10111)
            assert event.total_code == 21948

    def test_tokei_runner_parses_files(self) -> None:
        """Test runner parses file details."""
        from stats.collectors.tokei import run

        sample_output = (FIXTURES_DIR / 'tokei_sample.json').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=sample_output,
                stderr='',
            )

            event = run('master', 'ichrisbirch')

            python_files = event.languages['Python'].files
            assert len(python_files) == 2
            assert python_files[0].name == 'ichrisbirch/api/main.py'
