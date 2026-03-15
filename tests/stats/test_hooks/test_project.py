"""Tests for project-specific hooks (code-sync, generate-fixture-diagrams, validate-html)."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'tool_outputs'


class TestCodeSyncSchema:
    """Tests for CodeSyncHookEvent schema."""

    def test_code_sync_hook_event(self) -> None:
        from stats.schemas.hooks.project import CodeSyncHookEvent

        event = CodeSyncHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            files_checked=['docs/guide.md'],
            duration_seconds=1.0,
        )

        assert event.type == 'hook.code-sync'
        assert event.status == 'passed'

    def test_code_sync_hook_event_failed(self) -> None:
        """Test CodeSyncHookEvent with failing sync check."""
        from stats.schemas.hooks.project import CodeSyncHookEvent

        event = CodeSyncHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            files_checked=['docs/api.md'],
            duration_seconds=1.0,
        )

        assert event.type == 'hook.code-sync'
        assert event.status == 'failed'


class TestCodeSyncRunner:
    """Tests for code-sync hook runner."""

    def test_code_sync_runner_runs_command(self) -> None:
        from stats.hooks.code_sync import run
        from stats.schemas.hooks.project import CodeSyncHookEvent

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')

            event = run(['docs/guide.md'], 'master', 'ichrisbirch')

            assert isinstance(event, CodeSyncHookEvent)
            assert event.status == 'passed'

    def test_code_sync_runner_failed(self) -> None:
        """Test runner returns failed event for out-of-sync code blocks."""
        from stats.hooks.code_sync import run
        from stats.schemas.hooks.project import CodeSyncHookEvent

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout='Code block out of sync in docs/api.md:15',
                stderr='',
            )

            event = run(['docs/api.md'], 'master', 'ichrisbirch')

            assert isinstance(event, CodeSyncHookEvent)
            assert event.status == 'failed'
            assert event.exit_code == 1


class TestGenerateFixtureDiagramsSchema:
    """Tests for GenerateFixtureDiagramsHookEvent schema."""

    def test_generate_fixture_diagrams_hook_event(self) -> None:
        from stats.schemas.hooks.project import GenerateFixtureDiagramsHookEvent

        event = GenerateFixtureDiagramsHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            files_checked=['tests/conftest.py'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.generate-fixture-diagrams'

    def test_generate_fixture_diagrams_hook_event_failed(self) -> None:
        """Test GenerateFixtureDiagramsHookEvent with failing check."""
        from stats.schemas.hooks.project import GenerateFixtureDiagramsHookEvent

        event = GenerateFixtureDiagramsHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            files_checked=['tests/conftest.py'],
            duration_seconds=2.0,
        )

        assert event.type == 'hook.generate-fixture-diagrams'
        assert event.status == 'failed'


class TestGenerateFixtureDiagramsRunner:
    """Tests for generate-fixture-diagrams hook runner."""

    def test_generate_fixture_diagrams_runner_skips_irrelevant(self) -> None:
        from stats.hooks.generate_fixture_diagrams import run

        event = run(['main.py'], 'master', 'ichrisbirch')

        assert event.status == 'passed'
        assert not event.files_checked

    def test_generate_fixture_diagrams_runner_clean(self) -> None:
        """Test runner returns passed event for up-to-date diagrams."""
        from stats.hooks.generate_fixture_diagrams import run
        from stats.schemas.hooks.project import GenerateFixtureDiagramsHookEvent

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='Diagrams are up to date.',
                stderr='',
            )

            event = run(['tests/conftest.py'], 'master', 'ichrisbirch')

            assert isinstance(event, GenerateFixtureDiagramsHookEvent)
            assert event.status == 'passed'
            assert event.exit_code == 0

    def test_generate_fixture_diagrams_runner_failed(self) -> None:
        """Test runner returns failed event for outdated diagrams."""
        from stats.hooks.generate_fixture_diagrams import run
        from stats.schemas.hooks.project import GenerateFixtureDiagramsHookEvent

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout='Diagrams need regeneration.',
                stderr='',
            )

            event = run(['tests/conftest.py'], 'master', 'ichrisbirch')

            assert isinstance(event, GenerateFixtureDiagramsHookEvent)
            assert event.status == 'failed'
            assert event.exit_code == 1


class TestValidateHtmlSchema:
    """Tests for ValidateHtmlHookEvent schema."""

    def test_validate_html_hook_event_with_issues(self) -> None:
        from stats.schemas.hooks.project import HtmlValidationIssue
        from stats.schemas.hooks.project import ValidateHtmlHookEvent

        event = ValidateHtmlHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            issues=[
                HtmlValidationIssue(
                    file='templates/index.html',
                    line=15,
                    message='Element "div" not allowed',
                    level='ERROR',
                )
            ],
            files_checked=['templates/index.html'],
            duration_seconds=0.8,
        )

        assert event.type == 'hook.validate-html'
        assert len(event.issues) == 1

    def test_validate_html_hook_event_clean(self) -> None:
        """Test ValidateHtmlHookEvent with no issues."""
        from stats.schemas.hooks.project import ValidateHtmlHookEvent

        event = ValidateHtmlHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            issues=[],
            files_checked=['templates/index.html'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.validate-html'
        assert event.status == 'passed'
        assert not event.issues


class TestValidateHtmlRunner:
    """Tests for validate-html hook runner."""

    def test_validate_html_runner_parses_issues(self) -> None:
        from stats.hooks.validate_html import run
        from stats.schemas.hooks.project import ValidateHtmlHookEvent

        issues_output = (FIXTURES_DIR / 'validate_html_with_issues.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=issues_output,
                stderr='',
            )

            event = run(['ichrisbirch/app/templates/books/index.html'], 'master', 'ichrisbirch')

            assert isinstance(event, ValidateHtmlHookEvent)
            assert event.status == 'failed'
            assert len(event.issues) == 2
            assert event.issues[0].file == 'ichrisbirch/app/templates/books/index.html'
            assert event.issues[0].line == 15
            assert event.issues[0].level == 'ERROR'
            assert event.issues[1].file == 'ichrisbirch/app/templates/books/add.html'
            assert event.issues[1].level == 'WARNING'

    def test_validate_html_runner_clean(self) -> None:
        """Test runner returns passed event for valid HTML."""
        from stats.hooks.validate_html import run
        from stats.schemas.hooks.project import ValidateHtmlHookEvent

        clean_output = (FIXTURES_DIR / 'validate_html_clean.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=clean_output,
                stderr='',
            )

            event = run(['ichrisbirch/app/templates/books/index.html'], 'master', 'ichrisbirch')

            assert isinstance(event, ValidateHtmlHookEvent)
            assert event.status == 'passed'
            assert not event.issues

    def test_validate_html_runner_skips_non_html(self) -> None:
        from stats.hooks.validate_html import run

        event = run(['main.py'], 'master', 'ichrisbirch')

        assert event.status == 'passed'
        assert not event.files_checked
