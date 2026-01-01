"""Tests for file format validation hooks (check-yaml, check-toml, check-json)."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'tool_outputs'


class TestCheckYamlSchema:
    """Tests for CheckYamlHookEvent schema."""

    def test_check_yaml_hook_event_with_issues(self) -> None:
        """Test CheckYamlHookEvent with issues."""
        from stats.schemas.hooks.file_format import CheckYamlHookEvent
        from stats.schemas.hooks.file_format import FileFormatIssue

        event = CheckYamlHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            issues=[
                FileFormatIssue(
                    path='config.yaml',
                    line=10,
                    column=5,
                    message='mapping values are not allowed here',
                )
            ],
            files_checked=['config.yaml'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.check-yaml'
        assert event.status == 'failed'
        assert len(event.issues) == 1

    def test_check_yaml_hook_event_clean(self) -> None:
        """Test CheckYamlHookEvent with no issues."""
        from stats.schemas.hooks.file_format import CheckYamlHookEvent

        event = CheckYamlHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            issues=[],
            files_checked=['config.yaml'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.check-yaml'
        assert event.status == 'passed'
        assert not event.issues


class TestCheckYamlRunner:
    """Tests for check-yaml hook runner."""

    def test_check_yaml_runner_returns_typed_event_clean(self) -> None:
        """Test runner returns CheckYamlHookEvent for clean output."""
        from stats.hooks.check_yaml import run
        from stats.schemas.hooks.file_format import CheckYamlHookEvent

        clean_output = (FIXTURES_DIR / 'check_yaml_clean.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=clean_output,
                stderr='',
            )

            event = run(['config.yaml'], 'master', 'ichrisbirch')

            assert isinstance(event, CheckYamlHookEvent)
            assert event.status == 'passed'
            assert not event.issues

    def test_check_yaml_runner_parses_issues(self) -> None:
        """Test runner parses issues from check-yaml output."""
        from stats.hooks.check_yaml import run
        from stats.schemas.hooks.file_format import CheckYamlHookEvent

        issues_output = (FIXTURES_DIR / 'check_yaml_with_issues.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=issues_output,
                stderr='',
            )

            event = run(['config.yaml'], 'master', 'ichrisbirch')

            assert isinstance(event, CheckYamlHookEvent)
            assert event.status == 'failed'
            assert len(event.issues) == 2
            assert event.issues[0].path == 'config/settings.yaml'
            assert event.issues[0].line == 2

    def test_check_yaml_runner_filters_yaml_files(self) -> None:
        """Test runner only checks YAML files."""
        from stats.hooks.check_yaml import run

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')

            event = run(['config.yaml', 'main.py', 'settings.yml'], 'master', 'ichrisbirch')

            assert set(event.files_checked) == {'config.yaml', 'settings.yml'}


class TestCheckTomlSchema:
    """Tests for CheckTomlHookEvent schema."""

    def test_check_toml_hook_event_with_issues(self) -> None:
        """Test CheckTomlHookEvent with issues."""
        from stats.schemas.hooks.file_format import CheckTomlHookEvent
        from stats.schemas.hooks.file_format import FileFormatIssue

        event = CheckTomlHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            issues=[
                FileFormatIssue(
                    path='pyproject.toml',
                    line=1,
                    column=9,
                    message="Expected ']' at the end of a table declaration",
                )
            ],
            files_checked=['pyproject.toml'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.check-toml'
        assert event.status == 'failed'


class TestCheckTomlRunner:
    """Tests for check-toml hook runner."""

    def test_check_toml_runner_parses_issues(self) -> None:
        """Test runner parses issues from check-toml output."""
        from stats.hooks.check_toml import run
        from stats.schemas.hooks.file_format import CheckTomlHookEvent

        issues_output = (FIXTURES_DIR / 'check_toml_with_issues.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=issues_output,
                stderr='',
            )

            event = run(['pyproject.toml'], 'master', 'ichrisbirch')

            assert isinstance(event, CheckTomlHookEvent)
            assert event.status == 'failed'
            assert len(event.issues) == 2
            assert event.issues[0].path == 'pyproject.toml'
            assert event.issues[0].line == 1
            assert event.issues[0].column == 9

    def test_check_toml_runner_filters_toml_files(self) -> None:
        """Test runner only checks TOML files."""
        from stats.hooks.check_toml import run

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')

            event = run(['pyproject.toml', 'main.py', 'config.yaml'], 'master', 'ichrisbirch')

            assert event.files_checked == ['pyproject.toml']


class TestCheckJsonSchema:
    """Tests for CheckJsonHookEvent schema."""

    def test_check_json_hook_event_with_issues(self) -> None:
        """Test CheckJsonHookEvent with issues."""
        from stats.schemas.hooks.file_format import CheckJsonHookEvent
        from stats.schemas.hooks.file_format import FileFormatIssue

        event = CheckJsonHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            issues=[
                FileFormatIssue(
                    path='package.json',
                    line=1,
                    column=13,
                    message='Expecting value',
                )
            ],
            files_checked=['package.json'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.check-json'
        assert event.status == 'failed'


class TestCheckJsonRunner:
    """Tests for check-json hook runner."""

    def test_check_json_runner_parses_issues(self) -> None:
        """Test runner parses issues from check-json output."""
        from stats.hooks.check_json import run
        from stats.schemas.hooks.file_format import CheckJsonHookEvent

        issues_output = (FIXTURES_DIR / 'check_json_with_issues.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=issues_output,
                stderr='',
            )

            event = run(['package.json'], 'master', 'ichrisbirch')

            assert isinstance(event, CheckJsonHookEvent)
            assert event.status == 'failed'
            assert len(event.issues) == 2
            assert event.issues[0].path == 'package.json'
            assert event.issues[0].line == 1
            assert event.issues[0].column == 13

    def test_check_json_runner_filters_json_files(self) -> None:
        """Test runner only checks JSON files."""
        from stats.hooks.check_json import run

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')

            event = run(['package.json', 'main.py', 'data.json'], 'master', 'ichrisbirch')

            assert set(event.files_checked) == {'package.json', 'data.json'}
