"""Tests for sass hook schema and runner."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from unittest.mock import MagicMock
from unittest.mock import patch

from stats.hooks.sass import _parse_sass_errors
from stats.hooks.sass import run
from stats.schemas.hooks.sass import SassError
from stats.schemas.hooks.sass import SassHookEvent


class TestSassSchema:
    """Tests for SassHookEvent schema."""

    def test_sass_hook_event_with_errors(self) -> None:
        """Test SassHookEvent with compilation errors."""
        event = SassHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            issues=[SassError(message='Error: expected "{"', file='main.scss', line=3, column=15)],
            files_checked=['main.scss'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.sass'
        assert event.status == 'failed'
        assert len(event.issues) == 1

    def test_sass_hook_event_clean(self) -> None:
        """Test SassHookEvent with no issues."""
        event = SassHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            issues=[],
            files_checked=['main.scss'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.sass'
        assert event.status == 'passed'
        assert not event.issues

    def test_sass_hook_event_serializes_to_json(self) -> None:
        """Test SassHookEvent can be serialized to JSON."""
        event = SassHookEvent(
            timestamp=datetime(2025, 12, 31, 7, 36, 12, tzinfo=UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            issues=[],
            files_checked=['main.scss'],
            duration_seconds=0.5,
        )

        json_str = event.model_dump_json()
        assert '"type":"hook.sass"' in json_str
        assert '"status":"passed"' in json_str


class TestSassRunner:
    """Tests for sass hook runner."""

    def test_skips_non_scss_files(self) -> None:
        """Test runner skips when no SCSS files are staged."""
        event = run(['config.yaml', 'README.md'], 'master', 'ichrisbirch')

        assert event.status == 'passed'
        assert not event.files_checked

    def test_compilation_error_reports_failed(self) -> None:
        """Test runner reports failed when sass compilation fails."""
        error_output = (
            'Error: expected "{".\n'
            '  \u2577\n'
            '3 \u2502 .invalid-syntax\n'
            '  \u2502               ^\n'
            '  \u2575\n'
            '  ichrisbirch/app/static/sass/main.scss 3:15  root stylesheet\n'
        )

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout='',
                stderr=error_output,
            )

            event = run(['main.scss'], 'master', 'ichrisbirch')

            assert event.status == 'failed'
            assert event.exit_code == 1
            assert len(event.issues) == 1
            assert 'expected' in event.issues[0].message

    @patch('stats.hooks.sass.filecmp.cmp', return_value=True)
    @patch('stats.hooks.sass.Path')
    def test_css_up_to_date_reports_passed(self, mock_path_cls, mock_cmp) -> None:
        """Test runner reports passed when compiled CSS matches committed CSS."""
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_cls.return_value = mock_path_instance
        mock_path_cls.side_effect = lambda p: mock_path_instance

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='',
                stderr='',
            )
            with patch('tempfile.NamedTemporaryFile') as mock_tmp:
                mock_tmp.return_value.__enter__ = MagicMock(return_value=MagicMock(name='/tmp/test.css'))
                mock_tmp.return_value.__exit__ = MagicMock(return_value=False)

                event = run(['main.scss'], 'master', 'ichrisbirch')

                assert event.status == 'passed'

    @patch('stats.hooks.sass.filecmp.cmp', return_value=False)
    def test_stale_css_reports_failed(self, mock_cmp) -> None:
        """Test runner reports failed when compiled CSS differs from committed CSS."""
        with (
            patch('subprocess.run') as mock_run,
            patch('stats.hooks.sass.Path') as mock_path_cls,
        ):
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='',
                stderr='',
            )

            # Make Path().exists() return True for both tmp file and CSS file
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = True
            mock_path_cls.return_value = mock_path_instance

            event = run(['main.scss'], 'master', 'ichrisbirch')

            assert event.status == 'failed'
            assert event.exit_code == 1
            assert any('differs' in issue.message for issue in event.issues)

    def test_measures_duration(self) -> None:
        """Test runner measures execution duration."""
        with (
            patch('subprocess.run') as mock_run,
            patch('stats.hooks.sass.filecmp.cmp', return_value=True),
            patch('stats.hooks.sass.Path') as mock_path_cls,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = True
            mock_path_cls.return_value = mock_path_instance

            event = run(['main.scss'], 'master', 'ichrisbirch')

            assert event.duration_seconds >= 0


class TestSassErrorParser:
    """Tests for _parse_sass_errors."""

    def test_parses_error_with_location(self) -> None:
        """Test parsing error output with file location."""
        output = (
            'Error: expected "{".\n'
            '  \u2577\n'
            '3 \u2502 .invalid-syntax\n'
            '  \u2502               ^\n'
            '  \u2575\n'
            '  ichrisbirch/app/static/sass/main.scss 3:15  root stylesheet\n'
        )

        issues = _parse_sass_errors(output)

        assert len(issues) == 1
        assert issues[0].file == 'ichrisbirch/app/static/sass/main.scss'
        assert issues[0].line == 3
        assert issues[0].column == 15

    def test_parses_empty_output(self) -> None:
        """Test parsing empty stderr."""
        assert not _parse_sass_errors('')
        assert not _parse_sass_errors('   ')

    def test_parses_error_without_location(self) -> None:
        """Test parsing error output without file location info."""
        output = 'Error: Could not find an option named "bad-flag".\n'

        issues = _parse_sass_errors(output)

        assert len(issues) == 1
        assert 'bad-flag' in issues[0].message
        assert issues[0].file is None
        assert issues[0].line is None
