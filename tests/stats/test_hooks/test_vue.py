"""Tests for Vue hooks (vue-eslint, vue-prettier, vue-typecheck)."""

from __future__ import annotations

import json
from datetime import UTC
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'tool_outputs'


class TestVueEslintSchema:
    """Tests for VueEslintHookEvent schema."""

    def test_vue_eslint_hook_event_with_issues(self) -> None:
        """Test VueEslintHookEvent with issues from fixture."""
        from stats.schemas.hooks.vue import EslintMessage
        from stats.schemas.hooks.vue import VueEslintHookEvent

        raw = json.loads((FIXTURES_DIR / 'vue_eslint_with_issues.json').read_text())
        messages: list[EslintMessage] = []
        for file_result in raw:
            for msg in file_result.get('messages', []):
                messages.append(
                    EslintMessage(
                        rule_id=msg.get('ruleId'),
                        severity=msg['severity'],
                        message=msg['message'],
                        line=msg['line'],
                        column=msg['column'],
                        file=file_result['filePath'],
                    )
                )

        event = VueEslintHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            error_count=1,
            warning_count=1,
            fixable_error_count=0,
            fixable_warning_count=0,
            messages=messages,
            files_checked=['frontend/src/App.vue'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.vue-eslint'
        assert event.status == 'failed'
        assert len(event.messages) == 2
        assert event.error_count == 1
        assert event.warning_count == 1

    def test_vue_eslint_hook_event_clean(self) -> None:
        """Test VueEslintHookEvent with no issues."""
        from stats.schemas.hooks.vue import VueEslintHookEvent

        event = VueEslintHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            error_count=0,
            warning_count=0,
            fixable_error_count=0,
            fixable_warning_count=0,
            messages=[],
            files_checked=['frontend/src/App.vue'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.vue-eslint'
        assert event.status == 'passed'
        assert not event.messages


class TestVueEslintRunner:
    """Tests for vue-eslint hook runner."""

    def test_vue_eslint_runner_returns_typed_event_clean(self) -> None:
        """Test runner returns VueEslintHookEvent for clean output."""
        from stats.hooks.vue_eslint import run
        from stats.schemas.hooks.vue import VueEslintHookEvent

        clean_output = (FIXTURES_DIR / 'vue_eslint_clean.json').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=clean_output,
                stderr='',
            )

            event = run(['frontend/src/App.vue'], 'master', 'ichrisbirch')

            assert isinstance(event, VueEslintHookEvent)
            assert event.status == 'passed'
            assert event.exit_code == 0
            assert not event.messages
            assert event.error_count == 0

    def test_vue_eslint_runner_parses_issues(self) -> None:
        """Test runner parses issues from ESLint output."""
        from stats.hooks.vue_eslint import run
        from stats.schemas.hooks.vue import VueEslintHookEvent

        issues_output = (FIXTURES_DIR / 'vue_eslint_with_issues.json').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=issues_output,
                stderr='',
            )

            event = run(['frontend/src/App.vue'], 'master', 'ichrisbirch')

            assert isinstance(event, VueEslintHookEvent)
            assert event.status == 'failed'
            assert len(event.messages) == 2
            assert event.error_count == 1
            assert event.warning_count == 1

    def test_vue_eslint_runner_skips_non_vue_files(self) -> None:
        """Test runner skips non-Vue/TS files."""
        from stats.hooks.vue_eslint import run

        event = run(['main.py', 'config.yaml'], 'master', 'ichrisbirch')

        assert event.status == 'passed'
        assert not event.files_checked


class TestVuePrettierSchema:
    """Tests for VuePrettierHookEvent schema."""

    def test_vue_prettier_hook_event_with_reformatted(self) -> None:
        """Test VuePrettierHookEvent with files needing reformatting."""
        from stats.schemas.hooks.vue import VuePrettierHookEvent

        event = VuePrettierHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            files_reformatted=['src/components/Foo.vue', 'src/views/Bar.vue'],
            files_checked=['frontend/src/components/Foo.vue', 'frontend/src/views/Bar.vue'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.vue-prettier'
        assert event.status == 'failed'
        assert len(event.files_reformatted) == 2

    def test_vue_prettier_hook_event_clean(self) -> None:
        """Test VuePrettierHookEvent with no files needing reformatting."""
        from stats.schemas.hooks.vue import VuePrettierHookEvent

        event = VuePrettierHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            files_reformatted=[],
            files_checked=['frontend/src/App.vue'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.vue-prettier'
        assert event.status == 'passed'
        assert not event.files_reformatted


class TestVuePrettierRunner:
    """Tests for vue-prettier hook runner."""

    def test_vue_prettier_runner_clean(self) -> None:
        """Test runner returns passed event for well-formatted files."""
        from stats.hooks.vue_prettier import run
        from stats.schemas.hooks.vue import VuePrettierHookEvent

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='Checking formatting...\nAll matched files use Prettier code style!',
                stderr='',
            )

            event = run(['frontend/src/App.vue'], 'master', 'ichrisbirch')

            assert isinstance(event, VuePrettierHookEvent)
            assert event.status == 'passed'
            assert not event.files_reformatted

    def test_vue_prettier_runner_with_reformatted(self) -> None:
        """Test runner parses files needing reformatting from output."""
        from stats.hooks.vue_prettier import run
        from stats.schemas.hooks.vue import VuePrettierHookEvent

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout='Checking formatting...\n[warn] src/components/Foo.vue\n[warn] Code style issues found in the above file(s).',
                stderr='',
            )

            event = run(['frontend/src/components/Foo.vue'], 'master', 'ichrisbirch')

            assert isinstance(event, VuePrettierHookEvent)
            assert event.status == 'failed'
            assert len(event.files_reformatted) == 1
            assert event.files_reformatted[0] == 'src/components/Foo.vue'

    def test_vue_prettier_runner_skips_non_vue_files(self) -> None:
        """Test runner skips non-Vue/frontend files."""
        from stats.hooks.vue_prettier import run

        event = run(['main.py', 'config.yaml'], 'master', 'ichrisbirch')

        assert event.status == 'passed'
        assert not event.files_checked


class TestVueTypecheckSchema:
    """Tests for VueTypecheckHookEvent schema."""

    def test_vue_typecheck_hook_event_with_errors(self) -> None:
        """Test VueTypecheckHookEvent with type errors."""
        from stats.schemas.hooks.vue import TypecheckError
        from stats.schemas.hooks.vue import VueTypecheckHookEvent

        event = VueTypecheckHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            error_count=2,
            errors=[
                TypecheckError(
                    file='src/stores/books.ts',
                    line=15,
                    column=3,
                    code='TS2322',
                    message="Type 'string' is not assignable to type 'number'.",
                ),
                TypecheckError(
                    file='src/views/BooksView.vue',
                    line=42,
                    column=10,
                    code='TS2345',
                    message="Argument of type 'string' is not assignable to parameter of type 'number'.",
                ),
            ],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.vue-typecheck'
        assert event.status == 'failed'
        assert event.error_count == 2
        assert len(event.errors) == 2

    def test_vue_typecheck_hook_event_clean(self) -> None:
        """Test VueTypecheckHookEvent with no errors."""
        from stats.schemas.hooks.vue import VueTypecheckHookEvent

        event = VueTypecheckHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            error_count=0,
            errors=[],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.vue-typecheck'
        assert event.status == 'passed'
        assert not event.errors


class TestVueTypecheckRunner:
    """Tests for vue-typecheck hook runner."""

    def test_vue_typecheck_runner_clean(self) -> None:
        """Test runner returns passed event for clean type check."""
        from stats.hooks.vue_typecheck import run
        from stats.schemas.hooks.vue import VueTypecheckHookEvent

        clean_output = (FIXTURES_DIR / 'vue_typecheck_clean.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=clean_output,
                stderr='',
            )

            event = run(['frontend/src/App.vue'], 'master', 'ichrisbirch')

            assert isinstance(event, VueTypecheckHookEvent)
            assert event.status == 'passed'
            assert event.error_count == 0
            assert not event.errors

    def test_vue_typecheck_runner_parses_errors(self) -> None:
        """Test runner parses type errors from tsc output."""
        from stats.hooks.vue_typecheck import run
        from stats.schemas.hooks.vue import VueTypecheckHookEvent

        errors_output = (FIXTURES_DIR / 'vue_typecheck_with_errors.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=errors_output,
                stderr='',
            )

            event = run(['frontend/src/stores/books.ts'], 'master', 'ichrisbirch')

            assert isinstance(event, VueTypecheckHookEvent)
            assert event.status == 'failed'
            assert event.error_count == 2
            assert len(event.errors) == 2
            assert event.errors[0].file == 'src/stores/books.ts'
            assert event.errors[0].code == 'TS2322'
            assert event.errors[1].file == 'src/views/BooksView.vue'
            assert event.errors[1].code == 'TS2345'

    def test_vue_typecheck_runner_skips_non_vue_files(self) -> None:
        """Test runner skips non-Vue/TS files."""
        from stats.hooks.vue_typecheck import run

        event = run(['main.py', 'config.yaml'], 'master', 'ichrisbirch')

        assert event.status == 'passed'
        assert event.error_count == 0
