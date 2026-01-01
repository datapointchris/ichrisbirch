"""Tests for bandit hook schema and runner."""

from __future__ import annotations

import json
from datetime import UTC
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'tool_outputs'


class TestBanditSchema:
    """Tests for BanditHookEvent schema."""

    def test_bandit_issue_schema_parses_real_output(self) -> None:
        """Test that BanditIssue can parse real bandit output."""
        from stats.schemas.hooks.bandit import BanditIssue

        data = json.loads((FIXTURES_DIR / 'bandit_with_issues.json').read_text())
        results = data.get('results', [])

        if not results:
            return

        issue = BanditIssue.model_validate(results[0])

        assert issue.code == 'B101'
        assert issue.test_id == 'B101'
        assert issue.test_name == 'assert_used'
        assert issue.issue_severity == 'LOW'
        assert issue.issue_confidence == 'HIGH'
        assert issue.issue_cwe is not None
        assert issue.issue_cwe.id == 703

    def test_bandit_hook_event_with_issues(self) -> None:
        """Test BanditHookEvent with issues."""
        from stats.schemas.hooks.bandit import BanditHookEvent
        from stats.schemas.hooks.bandit import BanditIssue
        from stats.schemas.hooks.bandit import BanditMetrics

        data = json.loads((FIXTURES_DIR / 'bandit_with_issues.json').read_text())
        issues = [BanditIssue.model_validate(i) for i in data.get('results', [])]

        event = BanditHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            issues=issues,
            metrics=BanditMetrics(severity_low=2, confidence_high=2),
            files_checked=['test.py'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.bandit'
        assert event.status == 'failed'
        assert len(event.issues) == 2

    def test_bandit_hook_event_clean(self) -> None:
        """Test BanditHookEvent with no issues."""
        from stats.schemas.hooks.bandit import BanditHookEvent
        from stats.schemas.hooks.bandit import BanditMetrics

        event = BanditHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            issues=[],
            metrics=BanditMetrics(),
            files_checked=['test.py'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.bandit'
        assert event.status == 'passed'
        assert not event.issues


class TestBanditRunner:
    """Tests for bandit hook runner."""

    def test_bandit_runner_returns_typed_event_clean(self) -> None:
        """Test runner returns BanditHookEvent for clean output."""
        from stats.hooks.bandit import run
        from stats.schemas.hooks.bandit import BanditHookEvent

        clean_output = (FIXTURES_DIR / 'bandit_clean.json').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=clean_output,
                stderr='',
            )

            event = run(['test.py'], 'master', 'ichrisbirch')

            assert isinstance(event, BanditHookEvent)
            assert event.status == 'passed'
            assert event.exit_code == 0
            assert not event.issues

    def test_bandit_runner_parses_issues(self) -> None:
        """Test runner parses issues from bandit output."""
        from stats.hooks.bandit import run
        from stats.schemas.hooks.bandit import BanditHookEvent

        issues_output = (FIXTURES_DIR / 'bandit_with_issues.json').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=issues_output,
                stderr='',
            )

            event = run(['test.py'], 'master', 'ichrisbirch')

            assert isinstance(event, BanditHookEvent)
            assert event.status == 'failed'
            assert len(event.issues) == 2
            assert event.issues[0].code == 'B101'

    def test_bandit_runner_parses_metrics(self) -> None:
        """Test runner parses metrics from bandit output."""
        from stats.hooks.bandit import run

        issues_output = (FIXTURES_DIR / 'bandit_with_issues.json').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=issues_output,
                stderr='',
            )

            event = run(['test.py'], 'master', 'ichrisbirch')

            assert event.metrics.confidence_high == 2
            assert event.metrics.severity_low == 2
            assert event.metrics.loc == 8661
