"""Tests for CommitEvent schema."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime


class TestStagedFile:
    """Tests for StagedFile schema."""

    def test_staged_file_all_statuses(self) -> None:
        """Test StagedFile accepts all valid statuses."""
        from stats.schemas.commit import StagedFile

        for status in ('added', 'modified', 'deleted', 'renamed'):
            file = StagedFile(
                path='test.py',
                status=status,  # type: ignore[arg-type]
                lines_added=10,
                lines_removed=5,
            )
            assert file.status == status

    def test_staged_file_serialization(self) -> None:
        """Test StagedFile serializes correctly."""
        from stats.schemas.commit import StagedFile

        file = StagedFile(
            path='ichrisbirch/api/main.py',
            status='modified',
            lines_added=25,
            lines_removed=10,
        )

        data = file.model_dump()

        assert data['path'] == 'ichrisbirch/api/main.py'
        assert data['status'] == 'modified'
        assert data['lines_added'] == 25
        assert data['lines_removed'] == 10


class TestCommitEvent:
    """Tests for CommitEvent schema."""

    def test_commit_event_has_type(self) -> None:
        """Test CommitEvent has correct type literal."""
        from stats.schemas.commit import CommitEvent

        event = CommitEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            hash='abc123def456789012345678901234567890abcd',
            short_hash='abc123d',
            message='feat: add new feature',
            author='Chris Birch',
            email='datapointchris@gmail.com',
            files_changed=3,
            insertions=100,
            deletions=50,
            staged_files=[],
        )

        assert event.type == 'commit'

    def test_commit_event_with_staged_files(self) -> None:
        """Test CommitEvent with staged files."""
        from stats.schemas.commit import CommitEvent
        from stats.schemas.commit import StagedFile

        staged_files = [
            StagedFile(path='test.py', status='modified', lines_added=10, lines_removed=5),
            StagedFile(path='new.py', status='added', lines_added=50, lines_removed=0),
            StagedFile(path='old.py', status='deleted', lines_added=0, lines_removed=30),
        ]

        event = CommitEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='feature-branch',
            hash='abc123def456789012345678901234567890abcd',
            short_hash='abc123d',
            message='refactor: update modules',
            author='Chris Birch',
            email='datapointchris@gmail.com',
            files_changed=3,
            insertions=60,
            deletions=35,
            staged_files=staged_files,
        )

        assert len(event.staged_files) == 3
        assert event.staged_files[0].status == 'modified'
        assert event.staged_files[1].status == 'added'
        assert event.staged_files[2].status == 'deleted'

    def test_commit_event_serialization(self) -> None:
        """Test CommitEvent serializes to JSON correctly."""
        from stats.schemas.commit import CommitEvent
        from stats.schemas.commit import StagedFile

        event = CommitEvent(
            timestamp=datetime(2025, 12, 31, 12, 0, 0, tzinfo=UTC),
            project='ichrisbirch',
            branch='master',
            hash='abc123def456789012345678901234567890abcd',
            short_hash='abc123d',
            message='feat: add feature',
            author='Chris Birch',
            email='datapointchris@gmail.com',
            files_changed=1,
            insertions=10,
            deletions=5,
            staged_files=[
                StagedFile(path='test.py', status='modified', lines_added=10, lines_removed=5),
            ],
        )

        json_str = event.model_dump_json()

        assert '"type":"commit"' in json_str
        assert '"hash":"abc123def456789012345678901234567890abcd"' in json_str
        assert '"short_hash":"abc123d"' in json_str
        assert '"message":"feat: add feature"' in json_str
        assert '"staged_files":[' in json_str
