"""Tests for mypy hook schema and runner."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'tool_outputs'


class TestMypySchema:
    """Tests for MypyHookEvent schema."""

    def test_mypy_error_schema(self) -> None:
        """Test that MypyError captures all fields."""
        from stats.schemas.hooks.mypy import MypyError

        error = MypyError(
            filename='/path/to/file.py',
            line=10,
            column=5,
            severity='error',
            message='Unsupported operand types',
            code='operator',
        )

        assert error.filename == '/path/to/file.py'
        assert error.line == 10
        assert error.severity == 'error'
        assert error.code == 'operator'

    def test_mypy_hook_event_with_errors(self) -> None:
        """Test MypyHookEvent with errors."""
        from stats.schemas.hooks.mypy import MypyError
        from stats.schemas.hooks.mypy import MypyHookEvent

        event = MypyHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            errors=[
                MypyError(
                    filename='test.py',
                    line=10,
                    severity='error',
                    message='Test error',
                    code='test',
                )
            ],
            files_checked=['test.py'],
            duration_seconds=1.0,
        )

        assert event.type == 'hook.mypy'
        assert event.status == 'failed'
        assert len(event.errors) == 1

    def test_mypy_hook_event_clean(self) -> None:
        """Test MypyHookEvent with no errors."""
        from stats.schemas.hooks.mypy import MypyHookEvent

        event = MypyHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            errors=[],
            files_checked=['test.py'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.mypy'
        assert event.status == 'passed'
        assert not event.errors


class TestMypyRunner:
    """Tests for mypy hook runner."""

    def test_mypy_runner_returns_typed_event_clean(self) -> None:
        """Test runner returns MypyHookEvent for clean output."""
        from stats.hooks.mypy import run
        from stats.schemas.hooks.mypy import MypyHookEvent

        clean_output = (FIXTURES_DIR / 'mypy_clean.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=clean_output,
                stderr='',
            )

            event = run(['test.py'], 'master', 'ichrisbirch')

            assert isinstance(event, MypyHookEvent)
            assert event.status == 'passed'
            assert event.exit_code == 0

    def test_mypy_runner_parses_errors(self) -> None:
        """Test runner parses errors from mypy output."""
        from stats.hooks.mypy import run
        from stats.schemas.hooks.mypy import MypyHookEvent

        errors_output = (FIXTURES_DIR / 'mypy_with_errors.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=errors_output,
                stderr='',
            )

            event = run(['test.py'], 'master', 'ichrisbirch')

            assert isinstance(event, MypyHookEvent)
            assert event.status == 'failed'
            assert len(event.errors) == 2
            assert event.errors[0].severity == 'error'
            assert event.errors[0].code == 'operator'

    def test_mypy_runner_skips_notes(self) -> None:
        """Test runner skips note-level messages."""
        from stats.hooks.mypy import _parse_mypy_output

        output = """test.py:10: note: This is a note  [annotation-unchecked]
test.py:15: error: Actual error  [return-value]"""

        errors = _parse_mypy_output(output)

        # Should only have the error, not the note
        assert len(errors) == 1
        assert errors[0].severity == 'error'
