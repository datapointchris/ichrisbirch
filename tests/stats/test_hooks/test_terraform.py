"""Tests for Terraform hooks (terraform_validate, terraform_tflint, terraform_fmt, terraform_docs)."""

from __future__ import annotations

import json
from datetime import UTC
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'tool_outputs'


class TestTerraformValidateSchema:
    """Tests for TerraformValidateHookEvent schema."""

    def test_terraform_validate_hook_event(self) -> None:
        from stats.schemas.hooks.terraform import TerraformValidateHookEvent

        event = TerraformValidateHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            files_checked=['infra/main.tf'],
            duration_seconds=1.0,
        )

        assert event.type == 'hook.terraform-validate'
        assert event.status == 'passed'

    def test_terraform_validate_hook_event_failed(self) -> None:
        """Test TerraformValidateHookEvent with failing validation."""
        from stats.schemas.hooks.terraform import TerraformValidateHookEvent

        event = TerraformValidateHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            files_checked=['infra/main.tf', 'infra/variables.tf'],
            duration_seconds=1.2,
        )

        assert event.type == 'hook.terraform-validate'
        assert event.status == 'failed'
        assert len(event.files_checked) == 2


class TestTerraformValidateRunner:
    """Tests for terraform_validate hook runner."""

    def test_terraform_validate_runner_skips_non_tf(self) -> None:
        from stats.hooks.terraform_validate import run

        event = run(['main.py'], 'master', 'ichrisbirch')

        assert event.status == 'passed'
        assert not event.files_checked

    def test_terraform_validate_runner_clean(self) -> None:
        """Test runner returns passed event for valid terraform."""
        from stats.hooks.terraform_validate import run
        from stats.schemas.hooks.terraform import TerraformValidateHookEvent

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='{"valid": true}',
                stderr='',
            )

            event = run(['infra/main.tf'], 'master', 'ichrisbirch')

            assert isinstance(event, TerraformValidateHookEvent)
            assert event.status == 'passed'
            assert event.exit_code == 0

    def test_terraform_validate_runner_failed(self) -> None:
        """Test runner returns failed event for invalid terraform."""
        from stats.hooks.terraform_validate import run
        from stats.schemas.hooks.terraform import TerraformValidateHookEvent

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout='{"valid": false}',
                stderr='',
            )

            event = run(['infra/main.tf'], 'master', 'ichrisbirch')

            assert isinstance(event, TerraformValidateHookEvent)
            assert event.status == 'failed'
            assert event.exit_code == 1


class TestTerraformTflintSchema:
    """Tests for TerraformTflintHookEvent schema."""

    def test_terraform_tflint_hook_event_with_issues(self) -> None:
        from stats.schemas.hooks.terraform import TerraformTflintHookEvent
        from stats.schemas.hooks.terraform import TflintIssue

        event = TerraformTflintHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            issues=[
                TflintIssue(
                    rule='terraform_naming_convention',
                    message='resource name should be snake_case',
                    severity='warning',
                    file='main.tf',
                    line=10,
                )
            ],
            files_checked=['infra/main.tf'],
            duration_seconds=2.0,
        )

        assert event.type == 'hook.terraform-tflint'
        assert len(event.issues) == 1

    def test_terraform_tflint_hook_event_from_fixture(self) -> None:
        """Test TerraformTflintHookEvent with issues parsed from fixture."""
        from stats.schemas.hooks.terraform import TerraformTflintHookEvent
        from stats.schemas.hooks.terraform import TflintIssue

        raw = json.loads((FIXTURES_DIR / 'terraform_tflint_with_issues.json').read_text())
        issues: list[TflintIssue] = []
        for issue in raw['issues']:
            rule_data = issue.get('rule', {})
            range_data = issue.get('range', {})
            start_data = range_data.get('start', {})
            issues.append(
                TflintIssue(
                    rule=rule_data.get('name', ''),
                    message=issue.get('message', ''),
                    severity=rule_data.get('severity', ''),
                    file=range_data.get('filename'),
                    line=start_data.get('line'),
                )
            )

        event = TerraformTflintHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            issues=issues,
            files_checked=['infra/main.tf', 'infra/variables.tf'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.terraform-tflint'
        assert event.status == 'failed'
        assert len(event.issues) == 2
        assert event.issues[0].rule == 'terraform_naming_convention'
        assert event.issues[1].rule == 'terraform_unused_declarations'

    def test_terraform_tflint_hook_event_clean(self) -> None:
        """Test TerraformTflintHookEvent with no issues."""
        from stats.schemas.hooks.terraform import TerraformTflintHookEvent

        event = TerraformTflintHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            issues=[],
            files_checked=['infra/main.tf'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.terraform-tflint'
        assert event.status == 'passed'
        assert not event.issues


class TestTerraformTflintRunner:
    """Tests for terraform_tflint hook runner."""

    def test_terraform_tflint_runner_skips_non_tf(self) -> None:
        from stats.hooks.terraform_tflint import run

        event = run(['main.py'], 'master', 'ichrisbirch')

        assert event.status == 'passed'
        assert not event.issues

    def test_terraform_tflint_runner_clean(self) -> None:
        """Test runner returns passed event for clean tflint output."""
        from stats.hooks.terraform_tflint import run
        from stats.schemas.hooks.terraform import TerraformTflintHookEvent

        clean_output = (FIXTURES_DIR / 'terraform_tflint_clean.json').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=clean_output,
                stderr='',
            )

            event = run(['infra/main.tf'], 'master', 'ichrisbirch')

            assert isinstance(event, TerraformTflintHookEvent)
            assert event.status == 'passed'
            assert not event.issues

    def test_terraform_tflint_runner_parses_issues(self) -> None:
        """Test runner parses issues from tflint output."""
        from stats.hooks.terraform_tflint import run
        from stats.schemas.hooks.terraform import TerraformTflintHookEvent

        issues_output = (FIXTURES_DIR / 'terraform_tflint_with_issues.json').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=issues_output,
                stderr='',
            )

            event = run(['infra/main.tf'], 'master', 'ichrisbirch')

            assert isinstance(event, TerraformTflintHookEvent)
            assert event.status == 'failed'
            assert len(event.issues) == 2
            assert event.issues[0].rule == 'terraform_naming_convention'
            assert event.issues[0].file == 'main.tf'
            assert event.issues[1].rule == 'terraform_unused_declarations'
            assert event.issues[1].line == 5


class TestTerraformFmtSchema:
    """Tests for TerraformFmtHookEvent schema."""

    def test_terraform_fmt_hook_event(self) -> None:
        from stats.schemas.hooks.terraform import TerraformFmtHookEvent

        event = TerraformFmtHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            files_reformatted=['main.tf'],
            files_checked=['infra/main.tf'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.terraform-fmt'
        assert len(event.files_reformatted) == 1

    def test_terraform_fmt_hook_event_clean(self) -> None:
        """Test TerraformFmtHookEvent with no files needing reformatting."""
        from stats.schemas.hooks.terraform import TerraformFmtHookEvent

        event = TerraformFmtHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            files_reformatted=[],
            files_checked=['infra/main.tf'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.terraform-fmt'
        assert event.status == 'passed'
        assert not event.files_reformatted


class TestTerraformFmtRunner:
    """Tests for terraform_fmt hook runner."""

    def test_terraform_fmt_runner_skips_non_tf(self) -> None:
        from stats.hooks.terraform_fmt import run

        event = run(['main.py'], 'master', 'ichrisbirch')

        assert event.status == 'passed'
        assert not event.files_reformatted

    def test_terraform_fmt_runner_clean(self) -> None:
        """Test runner returns passed event for well-formatted files."""
        from stats.hooks.terraform_fmt import run
        from stats.schemas.hooks.terraform import TerraformFmtHookEvent

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='',
                stderr='',
            )

            event = run(['infra/main.tf'], 'master', 'ichrisbirch')

            assert isinstance(event, TerraformFmtHookEvent)
            assert event.status == 'passed'
            assert not event.files_reformatted

    def test_terraform_fmt_runner_with_reformatted(self) -> None:
        """Test runner parses files needing reformatting from output."""
        from stats.hooks.terraform_fmt import run
        from stats.schemas.hooks.terraform import TerraformFmtHookEvent

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=3,
                stdout='main.tf\nvariables.tf\n',
                stderr='',
            )

            event = run(['infra/main.tf', 'infra/variables.tf'], 'master', 'ichrisbirch')

            assert isinstance(event, TerraformFmtHookEvent)
            assert event.status == 'failed'
            assert len(event.files_reformatted) == 2


class TestTerraformDocsSchema:
    """Tests for TerraformDocsHookEvent schema."""

    def test_terraform_docs_hook_event(self) -> None:
        from stats.schemas.hooks.terraform import TerraformDocsHookEvent

        event = TerraformDocsHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            files_checked=['infra/main.tf'],
            duration_seconds=0.3,
        )

        assert event.type == 'hook.terraform-docs'
        assert event.status == 'passed'

    def test_terraform_docs_hook_event_failed(self) -> None:
        """Test TerraformDocsHookEvent with failing check."""
        from stats.schemas.hooks.terraform import TerraformDocsHookEvent

        event = TerraformDocsHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            files_checked=['infra/main.tf'],
            duration_seconds=1.0,
        )

        assert event.type == 'hook.terraform-docs'
        assert event.status == 'failed'


class TestTerraformDocsRunner:
    """Tests for terraform_docs hook runner."""

    def test_terraform_docs_runner_skips_non_tf(self) -> None:
        from stats.hooks.terraform_docs import run

        event = run(['main.py'], 'master', 'ichrisbirch')

        assert event.status == 'passed'
        assert not event.files_checked

    def test_terraform_docs_runner_clean(self) -> None:
        """Test runner returns passed event for up-to-date docs."""
        from stats.hooks.terraform_docs import run
        from stats.schemas.hooks.terraform import TerraformDocsHookEvent

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='',
                stderr='',
            )

            event = run(['infra/main.tf'], 'master', 'ichrisbirch')

            assert isinstance(event, TerraformDocsHookEvent)
            assert event.status == 'passed'
            assert event.exit_code == 0

    def test_terraform_docs_runner_failed(self) -> None:
        """Test runner returns failed event for outdated docs."""
        from stats.hooks.terraform_docs import run
        from stats.schemas.hooks.terraform import TerraformDocsHookEvent

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout='README.md is out of date',
                stderr='',
            )

            event = run(['infra/main.tf'], 'master', 'ichrisbirch')

            assert isinstance(event, TerraformDocsHookEvent)
            assert event.status == 'failed'
            assert event.exit_code == 1
