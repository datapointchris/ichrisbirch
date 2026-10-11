"""Tests for file format validation hooks (check-yaml, check-toml, check-json)."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

from stats.hooks import check_executables_have_shebangs
from stats.hooks import check_json
from stats.hooks import check_shebang_scripts_are_executable
from stats.hooks import check_toml
from stats.hooks import check_yaml
from stats.schemas.hooks.file_format import CheckExecutablesShebangsHookEvent
from stats.schemas.hooks.file_format import CheckJsonHookEvent
from stats.schemas.hooks.file_format import CheckShebangExecutableHookEvent
from stats.schemas.hooks.file_format import CheckTomlHookEvent
from stats.schemas.hooks.file_format import CheckYamlHookEvent
from stats.schemas.hooks.file_format import FileFormatIssue

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'tool_outputs'


class TestCheckYamlSchema:
    """Tests for CheckYamlHookEvent schema."""

    def test_check_yaml_hook_event_with_issues(self) -> None:
        """Test CheckYamlHookEvent with issues."""
        event = CheckYamlHookEvent(
            timestamp=dt.datetime.now(dt.UTC),
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
        event = CheckYamlHookEvent(
            timestamp=dt.datetime.now(dt.UTC),
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
        clean_output = (FIXTURES_DIR / 'check_yaml_clean.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=clean_output,
                stderr='',
            )

            event = check_yaml.run(['config.yaml'], 'master', 'ichrisbirch')

            assert isinstance(event, CheckYamlHookEvent)
            assert event.status == 'passed'
            assert not event.issues

    def test_check_yaml_runner_parses_issues(self) -> None:
        """Test runner parses issues from check-yaml output."""
        issues_output = (FIXTURES_DIR / 'check_yaml_with_issues.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=issues_output,
                stderr='',
            )

            event = check_yaml.run(['config.yaml'], 'master', 'ichrisbirch')

            assert isinstance(event, CheckYamlHookEvent)
            assert event.status == 'failed'
            assert len(event.issues) == 2
            assert event.issues[0].path == 'config/settings.yaml'
            assert event.issues[0].line == 2

    def test_check_yaml_runner_filters_yaml_files(self) -> None:
        """Test runner only checks YAML files."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')

            event = check_yaml.run(['config.yaml', 'main.py', 'settings.yml'], 'master', 'ichrisbirch')

            assert set(event.files_checked) == {'config.yaml', 'settings.yml'}


class TestCheckTomlSchema:
    """Tests for CheckTomlHookEvent schema."""

    def test_check_toml_hook_event_with_issues(self) -> None:
        """Test CheckTomlHookEvent with issues."""
        event = CheckTomlHookEvent(
            timestamp=dt.datetime.now(dt.UTC),
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
        issues_output = (FIXTURES_DIR / 'check_toml_with_issues.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=issues_output,
                stderr='',
            )

            event = check_toml.run(['pyproject.toml'], 'master', 'ichrisbirch')

            assert isinstance(event, CheckTomlHookEvent)
            assert event.status == 'failed'
            assert len(event.issues) == 2
            assert event.issues[0].path == 'pyproject.toml'
            assert event.issues[0].line == 1
            assert event.issues[0].column == 9

    def test_check_toml_runner_filters_toml_files(self) -> None:
        """Test runner only checks TOML files."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')

            event = check_toml.run(['pyproject.toml', 'main.py', 'config.yaml'], 'master', 'ichrisbirch')

            assert event.files_checked == ['pyproject.toml']


class TestCheckJsonSchema:
    """Tests for CheckJsonHookEvent schema."""

    def test_check_json_hook_event_with_issues(self) -> None:
        """Test CheckJsonHookEvent with issues."""
        event = CheckJsonHookEvent(
            timestamp=dt.datetime.now(dt.UTC),
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
        issues_output = (FIXTURES_DIR / 'check_json_with_issues.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=issues_output,
                stderr='',
            )

            event = check_json.run(['package.json'], 'master', 'ichrisbirch')

            assert isinstance(event, CheckJsonHookEvent)
            assert event.status == 'failed'
            assert len(event.issues) == 2
            assert event.issues[0].path == 'package.json'
            assert event.issues[0].line == 1
            assert event.issues[0].column == 13

    def test_check_json_runner_filters_json_files(self) -> None:
        """Test runner only checks JSON files."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')

            event = check_json.run(['package.json', 'main.py', 'data.json'], 'master', 'ichrisbirch')

            assert set(event.files_checked) == {'package.json', 'data.json'}


class TestCheckExecutablesShebangsSchema:
    """Tests for CheckExecutablesShebangsHookEvent schema."""

    def test_check_executables_shebangs_hook_event_with_issues(self) -> None:
        """Test CheckExecutablesShebangsHookEvent with files missing shebangs."""
        event = CheckExecutablesShebangsHookEvent(
            timestamp=dt.datetime.now(dt.UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            files_without_shebangs=['scripts/deploy.sh', 'scripts/backup.sh'],
            files_checked=['scripts/deploy.sh', 'scripts/backup.sh', 'scripts/run.sh'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.check-executables-have-shebangs'
        assert event.status == 'failed'
        assert len(event.files_without_shebangs) == 2

    def test_check_executables_shebangs_hook_event_clean(self) -> None:
        """Test CheckExecutablesShebangsHookEvent with no issues."""
        event = CheckExecutablesShebangsHookEvent(
            timestamp=dt.datetime.now(dt.UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            files_without_shebangs=[],
            files_checked=['scripts/deploy.sh'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.check-executables-have-shebangs'
        assert event.status == 'passed'
        assert not event.files_without_shebangs


class TestCheckExecutablesShebangsRunner:
    """Tests for check-executables-have-shebangs hook runner."""

    def test_check_executables_shebangs_runner_clean(self) -> None:
        """Test runner returns passed event for files with shebangs."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='',
                stderr='',
            )

            event = check_executables_have_shebangs.run(['scripts/deploy.sh'], 'master', 'ichrisbirch')

            assert isinstance(event, CheckExecutablesShebangsHookEvent)
            assert event.status == 'passed'
            assert not event.files_without_shebangs

    def test_check_executables_shebangs_runner_parses_issues(self) -> None:
        """Test runner parses files missing shebangs from output."""
        issues_output = (FIXTURES_DIR / 'check_executables_shebangs_with_issues.txt').read_text()

        with (
            patch('subprocess.run') as mock_run,
            patch('stats.hooks.check_executables_have_shebangs.os.access', return_value=True),
        ):
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=issues_output,
                stderr='',
            )

            event = check_executables_have_shebangs.run(['scripts/deploy.sh', 'scripts/backup.sh'], 'master', 'ichrisbirch')

            assert isinstance(event, CheckExecutablesShebangsHookEvent)
            assert event.status == 'failed'
            assert len(event.files_without_shebangs) == 2

    def test_check_executables_shebangs_runner_empty_staged(self) -> None:
        """Test runner returns passed event when no files are staged."""
        event = check_executables_have_shebangs.run([], 'master', 'ichrisbirch')

        assert event.status == 'passed'
        assert not event.files_checked


class TestCheckShebangExecutableSchema:
    """Tests for CheckShebangExecutableHookEvent schema."""

    def test_check_shebang_executable_hook_event_with_issues(self) -> None:
        """Test CheckShebangExecutableHookEvent with files not executable."""
        event = CheckShebangExecutableHookEvent(
            timestamp=dt.datetime.now(dt.UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            files_not_executable=['scripts/deploy.sh'],
            files_checked=['scripts/deploy.sh', 'scripts/run.sh'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.check-shebang-scripts-are-executable'
        assert event.status == 'failed'
        assert len(event.files_not_executable) == 1

    def test_check_shebang_executable_hook_event_clean(self) -> None:
        """Test CheckShebangExecutableHookEvent with no issues."""
        event = CheckShebangExecutableHookEvent(
            timestamp=dt.datetime.now(dt.UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            files_not_executable=[],
            files_checked=['scripts/deploy.sh'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.check-shebang-scripts-are-executable'
        assert event.status == 'passed'
        assert not event.files_not_executable


class TestCheckShebangExecutableRunner:
    """Tests for check-shebang-scripts-are-executable hook runner."""

    def test_check_shebang_executable_runner_clean(self) -> None:
        """Test runner returns passed event for executable scripts."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='',
                stderr='',
            )

            event = check_shebang_scripts_are_executable.run(['scripts/deploy.sh'], 'master', 'ichrisbirch')

            assert isinstance(event, CheckShebangExecutableHookEvent)
            assert event.status == 'passed'
            assert not event.files_not_executable

    def test_check_shebang_executable_runner_parses_issues(self) -> None:
        """Test runner parses files not executable from output."""
        issues_output = (FIXTURES_DIR / 'check_shebang_executable_with_issues.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=issues_output,
                stderr='',
            )

            event = check_shebang_scripts_are_executable.run(['scripts/deploy.sh'], 'master', 'ichrisbirch')

            assert isinstance(event, CheckShebangExecutableHookEvent)
            assert event.status == 'failed'
            assert len(event.files_not_executable) == 1

    def test_check_shebang_executable_runner_empty_staged(self) -> None:
        """Test runner returns passed event when no files are staged."""
        event = check_shebang_scripts_are_executable.run([], 'master', 'ichrisbirch')

        assert event.status == 'passed'
        assert not event.files_checked
