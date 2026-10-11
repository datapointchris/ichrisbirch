"""Tests for Terraform hooks (terraform_validate, terraform_tflint, terraform_fmt, terraform_docs)."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

from stats.hooks import terraform_docs
from stats.hooks import terraform_fmt
from stats.hooks import terraform_tflint
from stats.hooks import terraform_validate
from stats.schemas.hooks.terraform import TerraformDocsHookEvent
from stats.schemas.hooks.terraform import TerraformFmtHookEvent
from stats.schemas.hooks.terraform import TerraformTflintHookEvent
from stats.schemas.hooks.terraform import TerraformValidateHookEvent
from stats.schemas.hooks.terraform import TflintIssue

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'tool_outputs'


class TestTerraformValidateSchema:
    """Tests for TerraformValidateHookEvent schema."""

    def test_terraform_validate_hook_event(self) -> None:
        event = TerraformValidateHookEvent(
            timestamp=dt.datetime.now(dt.UTC),
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
        event = TerraformValidateHookEvent(
            timestamp=dt.datetime.now(dt.UTC),
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
        event = terraform_validate.run(['main.py'], 'master', 'ichrisbirch')

        assert event.status == 'passed'
        assert not event.files_checked

    def test_terraform_validate_runner_clean(self) -> None:
        """Test runner returns passed event for valid terraform."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='{"valid": true}',
                stderr='',
            )

            event = terraform_validate.run(['infra/main.tf'], 'master', 'ichrisbirch')

            assert isinstance(event, TerraformValidateHookEvent)
            assert event.status == 'passed'
            assert event.exit_code == 0

    def test_terraform_validate_runner_failed(self) -> None:
        """Test runner returns failed event for invalid terraform."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout='{"valid": false}',
                stderr='',
            )

            event = terraform_validate.run(['infra/main.tf'], 'master', 'ichrisbirch')

            assert isinstance(event, TerraformValidateHookEvent)
            assert event.status == 'failed'
            assert event.exit_code == 1


class TestTerraformTflintSchema:
    """Tests for TerraformTflintHookEvent schema."""

    def test_terraform_tflint_hook_event_with_issues(self) -> None:
        event = TerraformTflintHookEvent(
            timestamp=dt.datetime.now(dt.UTC),
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
            timestamp=dt.datetime.now(dt.UTC),
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
        event = TerraformTflintHookEvent(
            timestamp=dt.datetime.now(dt.UTC),
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
        event = terraform_tflint.run(['main.py'], 'master', 'ichrisbirch')

        assert event.status == 'passed'
        assert not event.issues

    def test_terraform_tflint_runner_clean(self) -> None:
        """Test runner returns passed event for clean tflint output."""
        clean_output = (FIXTURES_DIR / 'terraform_tflint_clean.json').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=clean_output,
                stderr='',
            )

            event = terraform_tflint.run(['infra/main.tf'], 'master', 'ichrisbirch')

            assert isinstance(event, TerraformTflintHookEvent)
            assert event.status == 'passed'
            assert not event.issues

    def test_terraform_tflint_runner_parses_issues(self) -> None:
        """Test runner parses issues from tflint output."""
        issues_output = (FIXTURES_DIR / 'terraform_tflint_with_issues.json').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=issues_output,
                stderr='',
            )

            event = terraform_tflint.run(['infra/main.tf'], 'master', 'ichrisbirch')

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
        event = TerraformFmtHookEvent(
            timestamp=dt.datetime.now(dt.UTC),
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
        event = TerraformFmtHookEvent(
            timestamp=dt.datetime.now(dt.UTC),
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
        event = terraform_fmt.run(['main.py'], 'master', 'ichrisbirch')

        assert event.status == 'passed'
        assert not event.files_reformatted

    def test_terraform_fmt_runner_clean(self) -> None:
        """Test runner returns passed event for well-formatted files."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='',
                stderr='',
            )

            event = terraform_fmt.run(['infra/main.tf'], 'master', 'ichrisbirch')

            assert isinstance(event, TerraformFmtHookEvent)
            assert event.status == 'passed'
            assert not event.files_reformatted

    def test_terraform_fmt_runner_with_reformatted(self) -> None:
        """Test runner parses files needing reformatting from output."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=3,
                stdout='main.tf\nvariables.tf\n',
                stderr='',
            )

            event = terraform_fmt.run(['infra/main.tf', 'infra/variables.tf'], 'master', 'ichrisbirch')

            assert isinstance(event, TerraformFmtHookEvent)
            assert event.status == 'failed'
            assert len(event.files_reformatted) == 2


class TestTerraformDocsSchema:
    """Tests for TerraformDocsHookEvent schema."""

    def test_terraform_docs_hook_event(self) -> None:
        event = TerraformDocsHookEvent(
            timestamp=dt.datetime.now(dt.UTC),
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
        event = TerraformDocsHookEvent(
            timestamp=dt.datetime.now(dt.UTC),
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
        event = terraform_docs.run(['main.py'], 'master', 'ichrisbirch')

        assert event.status == 'passed'
        assert not event.files_checked

    def test_terraform_docs_runner_clean(self) -> None:
        """Test runner returns passed event for up-to-date docs."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='',
                stderr='',
            )

            event = terraform_docs.run(['infra/main.tf'], 'master', 'ichrisbirch')

            assert isinstance(event, TerraformDocsHookEvent)
            assert event.status == 'passed'
            assert event.exit_code == 0

    def test_terraform_docs_runner_failed(self) -> None:
        """Test runner returns failed event for outdated docs."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout='README.md is out of date',
                stderr='',
            )

            event = terraform_docs.run(['infra/main.tf'], 'master', 'ichrisbirch')

            assert isinstance(event, TerraformDocsHookEvent)
            assert event.status == 'failed'
            assert event.exit_code == 1
