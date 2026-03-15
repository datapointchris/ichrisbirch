"""Tests for docker hooks (docker-compose-validate, hadolint)."""

from __future__ import annotations

import json
from datetime import UTC
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'tool_outputs'


class TestDockerComposeValidateSchema:
    """Tests for DockerComposeValidateHookEvent schema."""

    def test_docker_compose_validate_hook_event_passed(self) -> None:
        """Test DockerComposeValidateHookEvent with passing validation."""
        from stats.schemas.hooks.docker import DockerComposeValidateHookEvent

        event = DockerComposeValidateHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            files_checked=['docker-compose.yml'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.docker-compose-validate'
        assert event.status == 'passed'
        assert event.exit_code == 0
        assert event.files_checked == ['docker-compose.yml']

    def test_docker_compose_validate_hook_event_failed(self) -> None:
        """Test DockerComposeValidateHookEvent with failing validation."""
        from stats.schemas.hooks.docker import DockerComposeValidateHookEvent

        event = DockerComposeValidateHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            files_checked=['docker-compose.yml', 'docker-compose.dev.yml'],
            duration_seconds=1.2,
        )

        assert event.type == 'hook.docker-compose-validate'
        assert event.status == 'failed'
        assert len(event.files_checked) == 2


class TestDockerComposeValidateRunner:
    """Tests for docker-compose-validate hook runner."""

    def test_docker_compose_validate_runner_clean(self) -> None:
        """Test runner returns passed event for valid compose files."""
        from stats.hooks.docker_compose_validate import run
        from stats.schemas.hooks.docker import DockerComposeValidateHookEvent

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')

            event = run(['docker-compose.yml'], 'master', 'ichrisbirch')

            assert isinstance(event, DockerComposeValidateHookEvent)
            assert event.status == 'passed'
            assert event.exit_code == 0
            assert event.files_checked == ['docker-compose.yml']

    def test_docker_compose_validate_runner_failed(self) -> None:
        """Test runner returns failed event for invalid compose files."""
        from stats.hooks.docker_compose_validate import run
        from stats.schemas.hooks.docker import DockerComposeValidateHookEvent

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout='',
                stderr='services.api.image must be a string',
            )

            event = run(['docker-compose.yml'], 'master', 'ichrisbirch')

            assert isinstance(event, DockerComposeValidateHookEvent)
            assert event.status == 'failed'
            assert event.exit_code == 1

    def test_docker_compose_validate_runner_skips_non_compose_files(self) -> None:
        """Test runner skips non-compose files."""
        from stats.hooks.docker_compose_validate import run

        event = run(['main.py', 'config.yaml'], 'master', 'ichrisbirch')

        assert event.status == 'passed'
        assert not event.files_checked


class TestHadolintSchema:
    """Tests for HadolintHookEvent schema."""

    def test_hadolint_hook_event_with_issues(self) -> None:
        """Test HadolintHookEvent with issues from fixture."""
        from stats.schemas.hooks.docker import HadolintHookEvent
        from stats.schemas.hooks.docker import HadolintIssue

        raw_issues = json.loads((FIXTURES_DIR / 'hadolint_with_issues.json').read_text())
        issues = [HadolintIssue.model_validate(i) for i in raw_issues]

        event = HadolintHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            issues=issues,
            files_checked=['Dockerfile'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.hadolint'
        assert event.status == 'failed'
        assert len(event.issues) == 2
        assert event.issues[0].code == 'DL3008'
        assert event.issues[1].code == 'DL4006'

    def test_hadolint_hook_event_clean(self) -> None:
        """Test HadolintHookEvent with no issues."""
        from stats.schemas.hooks.docker import HadolintHookEvent

        event = HadolintHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            issues=[],
            files_checked=['Dockerfile'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.hadolint'
        assert event.status == 'passed'
        assert not event.issues


class TestHadolintRunner:
    """Tests for hadolint hook runner."""

    def test_hadolint_runner_returns_typed_event_clean(self) -> None:
        """Test runner returns HadolintHookEvent for clean output."""
        from stats.hooks.hadolint import run
        from stats.schemas.hooks.docker import HadolintHookEvent

        clean_output = (FIXTURES_DIR / 'hadolint_clean.json').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=clean_output,
                stderr='',
            )

            event = run(['Dockerfile'], 'master', 'ichrisbirch')

            assert isinstance(event, HadolintHookEvent)
            assert event.status == 'passed'
            assert event.exit_code == 0
            assert not event.issues

    def test_hadolint_runner_parses_issues(self) -> None:
        """Test runner parses issues from hadolint output."""
        from stats.hooks.hadolint import run
        from stats.schemas.hooks.docker import HadolintHookEvent

        issues_output = (FIXTURES_DIR / 'hadolint_with_issues.json').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=issues_output,
                stderr='',
            )

            event = run(['Dockerfile'], 'master', 'ichrisbirch')

            assert isinstance(event, HadolintHookEvent)
            assert event.status == 'failed'
            assert len(event.issues) == 2
            assert event.issues[0].code == 'DL3008'
            assert event.issues[0].line == 5
            assert event.issues[1].code == 'DL4006'

    def test_hadolint_runner_skips_non_dockerfiles(self) -> None:
        """Test runner skips non-Dockerfile files."""
        from stats.hooks.hadolint import run

        event = run(['main.py', 'config.yaml'], 'master', 'ichrisbirch')

        assert event.status == 'passed'
        assert not event.files_checked
