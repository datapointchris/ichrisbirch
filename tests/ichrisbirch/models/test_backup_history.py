"""Tests for BackupHistory and BackupRestore models."""

from datetime import UTC
from datetime import datetime

from ichrisbirch import models


class TestBackupHistory:
    def test_create_backup_history(self):
        """Test creating a BackupHistory instance."""
        backup = models.BackupHistory(
            filename='backup-2024-01-15T0130-scheduled.dump',
            description='scheduled',
            backup_type='scheduled',
            environment='development',
            created_at=datetime.now(UTC),
            success=True,
        )
        assert backup.filename == 'backup-2024-01-15T0130-scheduled.dump'
        assert backup.backup_type == 'scheduled'
        assert backup.success is True

    def test_backup_history_with_metadata(self):
        """Test BackupHistory with full metadata."""
        table_snapshot = {
            'tables': [
                {'schema_name': 'public', 'table_name': 'users', 'row_count': 100},
                {'schema_name': 'public', 'table_name': 'tasks', 'row_count': 500},
            ],
            'total_tables': 2,
            'total_rows': 600,
        }
        backup = models.BackupHistory(
            filename='backup-2024-01-15T0130-manual.dump',
            description='pre-migration',
            backup_type='manual',
            environment='production',
            created_at=datetime.now(UTC),
            size_bytes=1024000,
            duration_seconds=45.5,
            s3_key='production/postgres/backup-2024-01-15T0130-manual.dump',
            success=True,
            table_snapshot=table_snapshot,
            postgres_version='PostgreSQL 16.1',
            database_size_bytes=50000000,
            checksum='abc123def456',
        )
        assert backup.size_bytes == 1024000
        assert backup.table_snapshot['total_rows'] == 600
        assert backup.postgres_version == 'PostgreSQL 16.1'

    def test_backup_history_repr(self):
        """Test BackupHistory __repr__ method."""
        created = datetime(2024, 1, 15, 1, 30, tzinfo=UTC)
        backup = models.BackupHistory(
            filename='test.dump',
            description='test',
            backup_type='manual',
            environment='development',
            created_at=created,
            success=True,
        )
        repr_str = repr(backup)
        assert 'BackupHistory' in repr_str
        assert 'test.dump' in repr_str
        assert 'success=True' in repr_str


class TestBackupRestore:
    def test_create_backup_restore(self):
        """Test creating a BackupRestore instance."""
        restore = models.BackupRestore(
            backup_id=1,
            restored_at=datetime.now(UTC),
            restored_to_environment='development',
            success=True,
        )
        assert restore.backup_id == 1
        assert restore.restored_to_environment == 'development'
        assert restore.success is True

    def test_backup_restore_with_error(self):
        """Test BackupRestore with failure details."""
        restore = models.BackupRestore(
            backup_id=1,
            restored_at=datetime.now(UTC),
            restored_to_environment='testing',
            duration_seconds=120.5,
            success=False,
            error_message='Connection refused',
        )
        assert restore.success is False
        assert restore.error_message == 'Connection refused'
        assert restore.duration_seconds == 120.5

    def test_backup_restore_repr(self):
        """Test BackupRestore __repr__ method."""
        restored = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
        restore = models.BackupRestore(
            backup_id=5,
            restored_at=restored,
            restored_to_environment='production',
            success=True,
        )
        repr_str = repr(restore)
        assert 'BackupRestore' in repr_str
        assert 'backup_id=5' in repr_str
        assert 'success=True' in repr_str
