"""Tests for backup Pydantic schemas."""

from datetime import UTC
from datetime import datetime

import pytest
from pydantic import ValidationError

from ichrisbirch import schemas


class TestBackupCreate:
    """Test BackupCreate schema validation."""

    def test_valid_backup_create(self):
        """Test creating a valid BackupCreate."""
        backup = schemas.BackupCreate(
            description='pre-migration',
            upload_to_s3=True,
            save_local=False,
        )
        assert backup.description == 'pre-migration'
        assert backup.upload_to_s3 is True
        assert backup.save_local is False

    def test_description_sanitization_spaces(self):
        """Spaces are converted to hyphens."""
        backup = schemas.BackupCreate(description='pre migration backup')
        assert backup.description == 'pre-migration-backup'

    def test_description_sanitization_uppercase(self):
        """Uppercase is converted to lowercase."""
        backup = schemas.BackupCreate(description='PreMigration')
        assert backup.description == 'premigration'

    def test_description_sanitization_special_chars(self):
        """Special characters are removed."""
        backup = schemas.BackupCreate(description='test!@#backup')
        assert backup.description == 'testbackup'

    def test_description_sanitization_mixed(self):
        """Mixed input is properly sanitized."""
        backup = schemas.BackupCreate(description='Pre Migration! Test 123')
        assert backup.description == 'pre-migration-test-123'

    def test_description_too_long(self):
        """Description over 50 chars after cleaning is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            schemas.BackupCreate(description='a' * 100)
        assert 'Description must be 50 characters or less' in str(exc_info.value)

    def test_description_empty_after_cleaning(self):
        """Description that becomes empty after cleaning is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            schemas.BackupCreate(description='!@#$%^&*()')
        assert 'alphanumeric characters' in str(exc_info.value)

    def test_defaults(self):
        """Test default values."""
        backup = schemas.BackupCreate(description='test')
        assert backup.upload_to_s3 is True
        assert backup.save_local is False


class TestTableSnapshot:
    """Test TableSnapshot schema."""

    def test_valid_table_snapshot(self):
        """Test creating a valid TableSnapshot."""
        snapshot = schemas.TableSnapshot(
            schema_name='public',
            table_name='users',
            row_count=100,
        )
        assert snapshot.schema_name == 'public'
        assert snapshot.table_name == 'users'
        assert snapshot.row_count == 100


class TestTableSnapshotSummary:
    """Test TableSnapshotSummary schema."""

    def test_valid_summary(self):
        """Test creating a valid TableSnapshotSummary."""
        tables = [
            schemas.TableSnapshot(schema_name='public', table_name='users', row_count=100),
            schemas.TableSnapshot(schema_name='public', table_name='tasks', row_count=500),
        ]
        summary = schemas.TableSnapshotSummary(
            tables=tables,
            total_tables=2,
            total_rows=600,
        )
        assert len(summary.tables) == 2
        assert summary.total_tables == 2
        assert summary.total_rows == 600


class TestBackup:
    """Test Backup schema."""

    def test_valid_backup(self):
        """Test creating a valid Backup from attributes."""
        backup = schemas.Backup(
            id=1,
            filename='backup-2024-01-15.dump',
            description='scheduled',
            backup_type='scheduled',
            environment='development',
            created_at=datetime.now(UTC),
            success=True,
        )
        assert backup.id == 1
        assert backup.filename == 'backup-2024-01-15.dump'
        assert backup.success is True

    def test_backup_with_optional_fields(self):
        """Test Backup with all optional fields."""
        backup = schemas.Backup(
            id=1,
            filename='backup.dump',
            description='manual',
            backup_type='manual',
            environment='production',
            created_at=datetime.now(UTC),
            deleted_at=None,
            size_bytes=1024000,
            duration_seconds=45.5,
            s3_key='prod/postgres/backup.dump',
            local_path=None,
            success=True,
            error_message=None,
            table_snapshot={'tables': [], 'total_tables': 0, 'total_rows': 0},
            postgres_version='PostgreSQL 16.1',
            database_size_bytes=50000000,
            checksum='abc123',
            triggered_by_user_id=1,
            restores=[],
        )
        assert backup.size_bytes == 1024000
        assert backup.postgres_version == 'PostgreSQL 16.1'


class TestBackupResult:
    """Test BackupResult schema."""

    def test_successful_result(self):
        """Test a successful backup result."""
        result = schemas.BackupResult(
            success=True,
            filename='backup.dump',
            size_bytes=1024000,
            duration_seconds=30.5,
            s3_key='dev/postgres/backup.dump',
            created_at=datetime.now(UTC),
            checksum='abc123',
        )
        assert result.success is True
        assert result.filename == 'backup.dump'
        assert result.error_message is None

    def test_failed_result(self):
        """Test a failed backup result."""
        result = schemas.BackupResult(
            success=False,
            error_message='Connection refused',
            created_at=datetime.now(UTC),
        )
        assert result.success is False
        assert result.error_message == 'Connection refused'
        assert result.filename is None


class TestBackupRestoreSchema:
    """Test BackupRestoreSchema."""

    def test_valid_restore(self):
        """Test creating a valid restore schema."""
        restore = schemas.BackupRestoreSchema(
            id=1,
            backup_id=5,
            restored_at=datetime.now(UTC),
            restored_to_environment='development',
            duration_seconds=120.0,
            success=True,
        )
        assert restore.id == 1
        assert restore.backup_id == 5
        assert restore.success is True
