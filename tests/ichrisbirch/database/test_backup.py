"""Tests for DatabaseBackup class.

These tests use the test database (localhost:5434) to verify backup functionality.
"""

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ichrisbirch.database.backup import DatabaseBackup
from tests.utils.database import create_session
from tests.utils.database import test_settings


@pytest.fixture
def test_backup(tmp_path):
    """Create a DatabaseBackup instance configured for test environment."""
    return DatabaseBackup(
        source_host=test_settings.postgres.host,
        source_port=str(test_settings.postgres.port),
        source_username=test_settings.postgres.username,
        source_password=test_settings.postgres.password,
        base_dir=tmp_path,
        settings=test_settings,
    )


class TestDatabaseBackupInit:
    """Test DatabaseBackup initialization."""

    def test_init_with_custom_values(self, tmp_path):
        """Test initialization with custom values."""
        backup = DatabaseBackup(
            backup_bucket='custom-bucket',
            source_host='custom-host',
            source_port='5555',
            base_dir=tmp_path,
        )
        assert backup.backup_bucket == 'custom-bucket'
        assert backup.source_host == 'custom-host'
        assert backup.source_port == '5555'
        assert backup.base_dir == tmp_path


class TestDatabaseBackupMetadata:
    """Test metadata collection methods."""

    def test_get_table_snapshot(self, test_backup):
        """Verify table snapshot collects all tables with row counts."""
        snapshot = test_backup._get_table_snapshot()

        assert 'tables' in snapshot
        assert 'total_tables' in snapshot
        assert 'total_rows' in snapshot
        assert isinstance(snapshot['tables'], list)
        assert snapshot['total_tables'] > 0

        # Verify table structure
        if snapshot['tables']:
            table = snapshot['tables'][0]
            assert 'schema_name' in table
            assert 'table_name' in table
            assert 'row_count' in table

    def test_get_postgres_version(self, test_backup):
        """Verify postgres version is captured without truncation."""
        version = test_backup._get_postgres_version()

        assert 'PostgreSQL' in version
        # Version strings can be long (e.g., 88+ chars with compile info)
        # After fix, this should work without truncation
        assert len(version) > 0

    def test_get_database_size(self, test_backup):
        """Verify database size in bytes is captured."""
        size = test_backup._get_database_size()

        assert isinstance(size, int)
        assert size > 0


class TestDatabaseBackupChecksum:
    """Test checksum computation."""

    def test_compute_checksum(self, tmp_path):
        """Verify SHA256 checksum is computed correctly."""
        # Create a test file
        test_file = tmp_path / 'test.dump'
        test_content = b'test backup content'
        test_file.write_bytes(test_content)

        backup = DatabaseBackup()
        checksum = backup._compute_checksum(test_file)

        assert len(checksum) == 64  # SHA256 produces 64 hex characters
        # Verify it's a valid hex string
        int(checksum, 16)


class TestDatabaseBackupCreation:
    """Test backup file creation."""

    def test_backup_creates_file_locally(self, test_backup):
        """Verify pg_dump creates backup file."""
        with patch.object(test_backup, '_upload_to_s3') as mock_upload:
            record = test_backup.backup(
                description='test-local',
                upload=False,
                save_local=True,
                backup_type='manual',
            )

        assert record.success is True
        assert record.filename is not None
        assert record.filename.endswith('.dump')
        assert record.local_path is not None
        assert Path(record.local_path).exists()
        mock_upload.assert_not_called()

    def test_backup_saves_history_record(self, test_backup):
        """Verify BackupHistory record created with all metadata."""
        record = test_backup.backup(
            description='test-history',
            upload=False,
            save_local=True,
            backup_type='manual',
        )

        assert record.id is not None
        assert record.filename is not None
        assert record.description == 'test-history'
        assert record.backup_type == 'manual'
        assert record.environment == test_settings.ENVIRONMENT
        assert record.success is True
        assert record.size_bytes is not None
        assert record.size_bytes > 0
        assert record.duration_seconds is not None
        assert record.checksum is not None
        assert len(record.checksum) == 64
        assert record.table_snapshot is not None
        assert record.postgres_version is not None
        assert record.database_size_bytes is not None

    def test_backup_handles_long_postgres_version(self, test_backup):
        """Verify long version strings save without truncation."""
        record = test_backup.backup(
            description='test-version',
            upload=False,
            save_local=True,
            backup_type='manual',
        )

        # PostgreSQL version strings are typically 80-100 characters
        # This test verifies the fix for the varchar(50) issue
        assert record.postgres_version is not None
        assert len(record.postgres_version) > 50
        assert 'PostgreSQL' in record.postgres_version


class TestDatabaseBackupS3:
    """Test S3 upload functionality."""

    def test_backup_local_only_skips_s3(self, test_backup):
        """Verify upload=False skips S3 upload."""
        with patch('boto3.resource') as mock_boto:
            record = test_backup.backup(
                description='test-no-s3',
                upload=False,
                save_local=True,
                backup_type='manual',
            )

        assert record.success is True
        assert record.s3_key is None
        mock_boto.assert_not_called()

    def test_backup_uploads_to_s3(self, test_backup):
        """Verify backup uploads to S3 when enabled."""
        mock_bucket = MagicMock()
        with patch('boto3.resource') as mock_boto:
            mock_boto.return_value.Bucket.return_value = mock_bucket

            record = test_backup.backup(
                description='test-s3-upload',
                upload=True,
                save_local=False,
                backup_type='manual',
            )

        assert record.success is True
        assert record.s3_key is not None
        assert record.s3_key.endswith('.dump')
        mock_bucket.upload_fileobj.assert_called_once()

    def test_backup_deletes_local_after_s3_upload(self, test_backup):
        """Verify local file deleted when save_local=False."""
        mock_bucket = MagicMock()
        with patch('boto3.resource') as mock_boto:
            mock_boto.return_value.Bucket.return_value = mock_bucket

            record = test_backup.backup(
                description='test-delete-local',
                upload=True,
                save_local=False,
                backup_type='manual',
            )

        assert record.success is True
        assert record.local_path is None
        # Local file should be deleted
        local_files = list(test_backup.base_dir.rglob('*.dump'))
        assert len(local_files) == 0


class TestDatabaseBackupErrors:
    """Test error handling."""

    def test_backup_failure_records_error_message(self, tmp_path):
        """Verify error_message captured on failure."""
        backup = DatabaseBackup(
            base_dir=tmp_path,
            source_host='nonexistent-host',
            source_port='5432',
            settings=test_settings,
        )

        record = backup.backup(
            description='test-error',
            upload=False,
            save_local=True,
            backup_type='manual',
        )

        assert record.success is False
        assert record.error_message is not None
        assert record.id is not None
        assert record.filename is not None


class TestDatabaseBackupUserTracking:
    """Test user tracking functionality."""

    def test_backup_tracks_user_id(self, test_backup):
        """Verify triggered_by_user_id is recorded."""
        # Get a real user ID from the test database
        with create_session(test_settings) as session:
            from ichrisbirch import models

            user = session.query(models.User).first()
            user_id = user.id

        record = test_backup.backup(
            description='test-user',
            upload=False,
            save_local=True,
            backup_type='manual',
            user_id=user_id,
        )

        assert record.triggered_by_user_id == user_id

    def test_backup_without_user_id(self, test_backup):
        """Verify backup works without user_id (CLI/scheduled)."""
        record = test_backup.backup(
            description='test-no-user',
            upload=False,
            save_local=True,
            backup_type='scheduled',
        )

        assert record.triggered_by_user_id is None
        assert record.backup_type == 'scheduled'
