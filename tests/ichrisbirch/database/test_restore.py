"""Tests for DatabaseRestore class."""

from datetime import UTC
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

from ichrisbirch import models
from ichrisbirch.database.restore import DatabaseRestore
from tests.utils.database import create_session
from tests.utils.database import test_settings


class TestDatabaseRestoreInit:
    """Test DatabaseRestore initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default settings."""
        restore = DatabaseRestore(
            target_host='localhost',
            target_port='5432',
            target_username='postgres',
            target_password='postgres',
        )
        assert restore.backup_bucket == test_settings.aws.s3_backup_bucket
        assert restore.target_host == 'localhost'
        assert restore.target_port == '5432'

    def test_init_with_custom_values(self, tmp_path):
        """Test initialization with custom values."""
        restore = DatabaseRestore(
            backup_bucket='custom-bucket',
            target_host='custom-host',
            target_port='5555',
            target_username='custom-user',
            target_password='custom-pass',
            base_dir=tmp_path,
        )
        assert restore.backup_bucket == 'custom-bucket'
        assert restore.target_host == 'custom-host'
        assert restore.target_port == '5555'
        assert restore.base_dir == tmp_path


class TestDatabaseRestoreS3Download:
    """Test S3 download functionality."""

    def test_download_from_s3_specific_file(self, tmp_path):
        """Verify backup downloaded from S3 by filename."""
        restore = DatabaseRestore(
            target_host='localhost',
            target_port='5432',
            target_username='postgres',
            target_password='postgres',
            base_dir=tmp_path,
        )

        mock_bucket = MagicMock()

        # Mock download to write a file
        def mock_download(key, fileobj):
            fileobj.write(b'mock backup content')

        mock_bucket.download_fileobj.side_effect = mock_download

        with patch('boto3.resource') as mock_boto:
            mock_boto.return_value.Bucket.return_value = mock_bucket
            downloaded_path = restore._download_from_s3('test-backup.dump')

        assert downloaded_path.exists()
        assert downloaded_path.name == 'test-backup.dump'
        mock_bucket.download_fileobj.assert_called_once()

    def test_download_from_s3_latest(self, tmp_path):
        """Verify 'latest' downloads most recent backup."""
        restore = DatabaseRestore(
            target_host='localhost',
            target_port='5432',
            target_username='postgres',
            target_password='postgres',
            base_dir=tmp_path,
        )

        # Create mock S3 objects with different timestamps
        mock_obj1 = MagicMock()
        mock_obj1.key = 'testing/postgres/backup-old.dump'
        mock_obj1.last_modified = datetime(2024, 1, 1, tzinfo=UTC)

        mock_obj2 = MagicMock()
        mock_obj2.key = 'testing/postgres/backup-newest.dump'
        mock_obj2.last_modified = datetime(2024, 12, 31, tzinfo=UTC)

        mock_bucket = MagicMock()
        mock_bucket.objects.filter.return_value = [mock_obj1, mock_obj2]

        def mock_download(key, fileobj):
            fileobj.write(b'mock backup content')

        mock_bucket.download_fileobj.side_effect = mock_download

        with patch('boto3.resource') as mock_boto:
            mock_boto.return_value.Bucket.return_value = mock_bucket
            downloaded_path = restore._download_from_s3('latest')

        assert downloaded_path.name == 'backup-newest.dump'


class TestDatabaseRestoreSkipDownload:
    """Test skip_download functionality."""

    def test_restore_skip_download_uses_local_file(self, tmp_path):
        """Verify skip_download uses local path directly."""
        # Create a mock backup file
        local_file = tmp_path / 'local-backup.dump'
        local_file.write_bytes(b'mock backup content')

        restore = DatabaseRestore(
            target_host='localhost',
            target_port='5432',
            target_username='postgres',
            target_password='postgres',
            base_dir=tmp_path,
            settings=test_settings,
        )

        with patch.object(restore, '_download_from_s3') as mock_download, patch.object(restore, '_restore_database') as mock_restore:
            mock_restore.return_value = None

            record = restore.restore(
                filename=str(local_file),
                skip_download=True,
            )

        mock_download.assert_not_called()
        mock_restore.assert_called_once()
        assert record.success is True


class TestDatabaseRestoreRecordLookup:
    """Test backup history record lookup."""

    def test_find_backup_record_exists(self):
        """Verify existing BackupHistory record found by filename."""
        # Create a backup record first
        import tempfile

        from ichrisbirch.database.backup import DatabaseBackup

        with tempfile.TemporaryDirectory() as tmp:
            backup = DatabaseBackup(
                base_dir=Path(tmp),
                source_host=test_settings.postgres.host,
                source_port=str(test_settings.postgres.port),
                source_username=test_settings.postgres.username,
                source_password=test_settings.postgres.password,
                settings=test_settings,
            )
            backup_record = backup.backup(
                description='lookup-test',
                upload=False,
                save_local=True,
                backup_type='manual',
            )

            restore = DatabaseRestore(
                target_host='localhost',
                target_port='5432',
                target_username='postgres',
                target_password='postgres',
                settings=test_settings,
            )

            found = restore._find_backup_record(backup_record.filename)

            assert found is not None
            assert found.filename == backup_record.filename

    def test_find_backup_record_not_found(self):
        """Verify None returned for unknown filename."""
        restore = DatabaseRestore(
            target_host='localhost',
            target_port='5432',
            target_username='postgres',
            target_password='postgres',
            settings=test_settings,
        )

        found = restore._find_backup_record('nonexistent-backup.dump')

        assert found is None


class TestDatabaseRestoreRecordCreation:
    """Test restore record creation."""

    def test_restore_saves_restore_record(self, tmp_path):
        """Verify BackupRestore record created with metadata."""
        # Create a mock backup file
        local_file = tmp_path / 'test-backup.dump'
        local_file.write_bytes(b'mock backup content')

        restore = DatabaseRestore(
            target_host='localhost',
            target_port='5432',
            target_username='postgres',
            target_password='postgres',
            base_dir=tmp_path,
            settings=test_settings,
        )

        with patch.object(restore, '_restore_database') as mock_restore:
            mock_restore.return_value = None

            record = restore.restore(
                filename=str(local_file),
                skip_download=True,
            )

        assert record.id is not None
        assert record.restored_to_environment == test_settings.ENVIRONMENT
        assert record.success is True
        assert record.duration_seconds is not None

    def test_restore_creates_stub_for_untracked_backup(self, tmp_path):
        """Verify stub BackupHistory created for unknown backups."""
        # Create a mock backup file with a name that doesn't exist in DB
        local_file = tmp_path / 'untracked-backup-xyz123.dump'
        local_file.write_bytes(b'mock backup content')

        restore = DatabaseRestore(
            target_host='localhost',
            target_port='5432',
            target_username='postgres',
            target_password='postgres',
            base_dir=tmp_path,
            settings=test_settings,
        )

        with patch.object(restore, '_restore_database') as mock_restore:
            mock_restore.return_value = None

            record = restore.restore(
                filename=str(local_file),
                skip_download=True,
            )

        assert record.backup_id is not None
        # Verify stub backup was created
        with create_session(test_settings) as session:
            backup = session.get(models.BackupHistory, record.backup_id)
            assert backup is not None
            assert backup.description == 'untracked-restore'
            assert backup.backup_type == 'unknown'


class TestDatabaseRestoreErrors:
    """Test error handling."""

    def test_restore_failure_records_error_message(self, tmp_path):
        """Verify error_message captured on restore failure."""
        local_file = tmp_path / 'test-backup.dump'
        local_file.write_bytes(b'mock backup content')

        restore = DatabaseRestore(
            target_host='nonexistent-host',
            target_port='5432',
            target_username='postgres',
            target_password='postgres',
            base_dir=tmp_path,
            settings=test_settings,
        )

        record = restore.restore(
            filename=str(local_file),
            skip_download=True,
        )

        assert record.success is False
        assert record.error_message is not None
        assert record.id is not None


class TestDatabaseRestoreUserTracking:
    """Test user tracking functionality."""

    def test_restore_tracks_user_id(self, tmp_path):
        """Verify restored_by_user_id is recorded."""
        local_file = tmp_path / 'test-backup.dump'
        local_file.write_bytes(b'mock backup content')

        # Get a real user ID from the test database
        with create_session(test_settings) as session:
            user = session.query(models.User).first()
            user_id = user.id

        restore = DatabaseRestore(
            target_host='localhost',
            target_port='5432',
            target_username='postgres',
            target_password='postgres',
            base_dir=tmp_path,
            settings=test_settings,
        )

        with patch.object(restore, '_restore_database') as mock_restore:
            mock_restore.return_value = None

            record = restore.restore(
                filename=str(local_file),
                skip_download=True,
                user_id=user_id,
            )

        assert record.restored_by_user_id == user_id

    def test_restore_without_user_id(self, tmp_path):
        """Verify restore works without user_id (CLI)."""
        local_file = tmp_path / 'test-backup.dump'
        local_file.write_bytes(b'mock backup content')

        restore = DatabaseRestore(
            target_host='localhost',
            target_port='5432',
            target_username='postgres',
            target_password='postgres',
            base_dir=tmp_path,
            settings=test_settings,
        )

        with patch.object(restore, '_restore_database') as mock_restore:
            mock_restore.return_value = None

            record = restore.restore(
                filename=str(local_file),
                skip_download=True,
            )

        assert record.restored_by_user_id is None


class TestDatabaseRestoreDeleteLocal:
    """Test local file deletion functionality."""

    def test_restore_delete_local_removes_file(self, tmp_path):
        """Verify delete_local removes downloaded file."""
        # Create mock download directory structure
        download_dir = tmp_path / 'ichrisbirch-backups' / 'testing' / 'postgres'
        download_dir.mkdir(parents=True)
        local_file = download_dir / 'test-backup.dump'
        local_file.write_bytes(b'mock backup content')

        restore = DatabaseRestore(
            target_host='localhost',
            target_port='5432',
            target_username='postgres',
            target_password='postgres',
            base_dir=tmp_path,
            settings=test_settings,
        )

        with patch.object(restore, '_restore_database') as mock_restore:
            mock_restore.return_value = None

            # Patch _download_from_s3 to return our local file
            with patch.object(restore, '_download_from_s3', return_value=local_file):
                restore.restore(
                    filename='test-backup.dump',
                    skip_download=False,  # Would normally download
                    delete_local=True,
                )

        # File should be deleted
        assert not local_file.exists()
