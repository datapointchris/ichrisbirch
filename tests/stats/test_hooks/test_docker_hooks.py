"""Tests for docker hooks (docker-compose-validate, hadolint)."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

from stats.hooks import docker_compose_validate
from stats.hooks import hadolint
from stats.schemas.hooks.docker import DockerComposeValidateHookEvent
from stats.schemas.hooks.docker import HadolintHookEvent
from stats.schemas.hooks.docker import HadolintIssue

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'tool_outputs'


class TestDockerComposeValidateSchema:
    """Tests for DockerComposeValidateHookEvent schema."""

    def test_docker_compose_validate_hook_event_passed(self) -> None:
        """Test DockerComposeValidateHookEvent with passing validation."""
        event = DockerComposeValidateHookEvent(
            timestamp=dt.datetime.now(dt.UTC),
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
        event = DockerComposeValidateHookEvent(
            timestamp=dt.datetime.now(dt.UTC),
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
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')

            event = docker_compose_validate.run(['docker-compose.yml'], 'master', 'ichrisbirch')

            assert isinstance(event, DockerComposeValidateHookEvent)
            assert event.status == 'passed'
            assert event.exit_code == 0
            assert event.files_checked == ['docker-compose.yml']

    def test_docker_compose_validate_runner_failed(self) -> None:
        """Test runner returns failed event for invalid compose files."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout='',
                stderr='services.api.image must be a string',
            )

            event = docker_compose_validate.run(['docker-compose.yml'], 'master', 'ichrisbirch')

            assert isinstance(event, DockerComposeValidateHookEvent)
            assert event.status == 'failed'
            assert event.exit_code == 1

    def test_docker_compose_validate_runner_skips_non_compose_files(self) -> None:
        """Test runner skips non-compose files."""
        event = docker_compose_validate.run(['main.py', 'config.yaml'], 'master', 'ichrisbirch')

        assert event.status == 'passed'
        assert not event.files_checked


class TestHadolintSchema:
    """Tests for HadolintHookEvent schema."""

    def test_hadolint_hook_event_with_issues(self) -> None:
        """Test HadolintHookEvent with issues from fixture."""
        raw_issues = json.loads((FIXTURES_DIR / 'hadolint_with_issues.json').read_text())
        issues = [HadolintIssue.model_validate(i) for i in raw_issues]

        event = HadolintHookEvent(
            timestamp=dt.datetime.now(dt.UTC),
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
        event = HadolintHookEvent(
            timestamp=dt.datetime.now(dt.UTC),
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
        clean_output = (FIXTURES_DIR / 'hadolint_clean.json').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=clean_output,
                stderr='',
            )

            event = hadolint.run(['Dockerfile'], 'master', 'ichrisbirch')

            assert isinstance(event, HadolintHookEvent)
            assert event.status == 'passed'
            assert event.exit_code == 0
            assert not event.issues

    def test_hadolint_runner_parses_issues(self) -> None:
        """Test runner parses issues from hadolint output."""
        issues_output = (FIXTURES_DIR / 'hadolint_with_issues.json').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=issues_output,
                stderr='',
            )

            event = hadolint.run(['Dockerfile'], 'master', 'ichrisbirch')

            assert isinstance(event, HadolintHookEvent)
            assert event.status == 'failed'
            assert len(event.issues) == 2
            assert event.issues[0].code == 'DL3008'
            assert event.issues[0].line == 5
            assert event.issues[1].code == 'DL4006'

    def test_hadolint_runner_skips_non_dockerfiles(self) -> None:
        """Test runner skips non-Dockerfile files."""
        event = hadolint.run(['main.py', 'config.yaml'], 'master', 'ichrisbirch')

        assert event.status == 'passed'
        assert not event.files_checked
