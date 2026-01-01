"""Tests for detect-private-key hook schema and runner."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'tool_outputs'


class TestDetectPrivateKeySchema:
    """Tests for DetectPrivateKeyHookEvent schema."""

    def test_detect_private_key_event_with_issues(self) -> None:
        """Test DetectPrivateKeyHookEvent with detected keys."""
        from stats.schemas.hooks.detect_private_key import DetectedPrivateKey
        from stats.schemas.hooks.detect_private_key import DetectPrivateKeyHookEvent

        event = DetectPrivateKeyHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            issues=[
                DetectedPrivateKey(path='certs/dev.key'),
                DetectedPrivateKey(path='certs/test.key'),
            ],
            files_checked=['certs/dev.key', 'certs/test.key', 'README.md'],
            duration_seconds=0.1,
        )

        assert event.type == 'hook.detect-private-key'
        assert event.status == 'failed'
        assert len(event.issues) == 2
        assert event.issues[0].path == 'certs/dev.key'

    def test_detect_private_key_event_clean(self) -> None:
        """Test DetectPrivateKeyHookEvent with no issues."""
        from stats.schemas.hooks.detect_private_key import DetectPrivateKeyHookEvent

        event = DetectPrivateKeyHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            issues=[],
            files_checked=['README.md', 'pyproject.toml'],
            duration_seconds=0.05,
        )

        assert event.type == 'hook.detect-private-key'
        assert event.status == 'passed'
        assert not event.issues


class TestDetectPrivateKeyRunner:
    """Tests for detect-private-key hook runner."""

    def test_runner_returns_typed_event_clean(self) -> None:
        """Test runner returns DetectPrivateKeyHookEvent for clean output."""
        from stats.hooks.detect_private_key import run
        from stats.schemas.hooks.detect_private_key import DetectPrivateKeyHookEvent

        clean_output = (FIXTURES_DIR / 'detect_private_key_clean.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=clean_output,
                stderr='',
            )

            event = run(['README.md'], 'master', 'ichrisbirch')

            assert isinstance(event, DetectPrivateKeyHookEvent)
            assert event.status == 'passed'
            assert event.exit_code == 0
            assert not event.issues

    def test_runner_parses_detected_keys(self) -> None:
        """Test runner parses detected private keys from output."""
        from stats.hooks.detect_private_key import run
        from stats.schemas.hooks.detect_private_key import DetectPrivateKeyHookEvent

        issues_output = (FIXTURES_DIR / 'detect_private_key_with_issues.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=issues_output,
                stderr='',
            )

            event = run(['certs/dev.key', 'certs/test.key'], 'master', 'ichrisbirch')

            assert isinstance(event, DetectPrivateKeyHookEvent)
            assert event.status == 'failed'
            assert len(event.issues) == 2
            assert event.issues[0].path == 'deploy-containers/traefik/certs/dev.key'
            assert event.issues[1].path == 'deploy-containers/traefik/certs/test.key'

    def test_runner_empty_files_returns_passed(self) -> None:
        """Test runner returns passed event when no files provided."""
        from stats.hooks.detect_private_key import run
        from stats.schemas.hooks.detect_private_key import DetectPrivateKeyHookEvent

        event = run([], 'master', 'ichrisbirch')

        assert isinstance(event, DetectPrivateKeyHookEvent)
        assert event.status == 'passed'
        assert event.exit_code == 0
        assert not event.issues
        assert not event.files_checked
