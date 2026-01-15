"""Tests for admin backup API endpoints.

These tests verify the API layer: authentication, authorization, validation,
and response handling. DatabaseBackup is mocked to isolate the API layer.

For real backup/restore integration tests, see:
- tests/ichrisbirch/database/test_backup.py
- tests/ichrisbirch/database/test_restore.py
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import pendulum
import pytest
from fastapi import status

from ichrisbirch import models
from tests.util import show_status_and_response

ENDPOINT = '/admin/backups/'


def make_backup_record(**overrides):
    """Create a BackupHistory model instance for testing API responses."""
    defaults = {
        'id': 1,
        'filename': 'backup-2026-01-15T1200-test.dump',
        'description': 'test',
        'backup_type': 'manual',
        'environment': 'testing',
        'created_at': pendulum.now(),
        'deleted_at': None,
        'size_bytes': 12345,
        'duration_seconds': 1.5,
        's3_key': None,
        'local_path': '/tmp/backup.dump',
        'success': True,
        'error_message': None,
        'table_snapshot': {'tables': [], 'total_tables': 10, 'total_rows': 100},
        'postgres_version': 'PostgreSQL 16.11 on x86_64-pc-linux-musl, compiled by gcc (Alpine 14.2.0) 14.2.0, 64-bit',
        'database_size_bytes': 1000000,
        'checksum': 'a' * 64,
        'triggered_by_user_id': None,
    }
    defaults.update(overrides)
    record = MagicMock(spec=models.BackupHistory)
    for key, value in defaults.items():
        setattr(record, key, value)
    return record


class TestBackupEndpointAuth:
    """Test backup endpoint authentication and authorization."""

    def test_read_backups_requires_admin(self, test_api_logged_in):
        """Regular users cannot access backup history."""
        response = test_api_logged_in.get(ENDPOINT)
        assert response.status_code == status.HTTP_403_FORBIDDEN, show_status_and_response(response)

    def test_read_backups_admin(self, test_api_logged_in_admin):
        """Admin users can access backup history."""
        response = test_api_logged_in_admin.get(ENDPOINT)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert isinstance(response.json(), list)

    def test_create_backup_requires_admin(self, test_api_logged_in):
        """Regular users cannot create backups."""
        response = test_api_logged_in.post(
            ENDPOINT,
            json={'description': 'test', 'upload_to_s3': True, 'save_local': False},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN, show_status_and_response(response)


class TestBackupEndpointValidation:
    """Test backup endpoint input validation."""

    def test_create_backup_validation_no_destination(self, test_api_logged_in_admin):
        """Creating backup without destination should fail."""
        response = test_api_logged_in_admin.post(
            ENDPOINT,
            json={'description': 'test', 'upload_to_s3': False, 'save_local': False},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST, show_status_and_response(response)
        assert 'At least one' in response.json()['detail']

    def test_create_backup_validation_empty_description(self, test_api_logged_in_admin):
        """Creating backup with empty description should fail validation."""
        response = test_api_logged_in_admin.post(
            ENDPOINT,
            json={'description': '', 'upload_to_s3': True, 'save_local': False},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, show_status_and_response(response)

    def test_get_backup_not_found(self, test_api_logged_in_admin):
        """GET /admin/backups/{id}/ returns 404 for nonexistent ID."""
        response = test_api_logged_in_admin.get(f'{ENDPOINT}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)


class TestBackupSchemaValidation:
    """Test backup schema validation."""

    def test_description_sanitization(self):
        """Test that description is sanitized correctly."""
        from ichrisbirch.schemas.backup import BackupCreate

        backup = BackupCreate(description='Pre Migration')
        assert backup.description == 'pre-migration'

        backup2 = BackupCreate(description='Test 123!')
        assert backup2.description == 'test-123'

    def test_description_too_long(self):
        """Test that long descriptions are rejected."""
        from pydantic import ValidationError

        from ichrisbirch.schemas.backup import BackupCreate

        with pytest.raises(ValidationError):
            BackupCreate(description='a' * 100)

    def test_description_only_special_chars(self):
        """Test that description with only special chars is rejected."""
        from pydantic import ValidationError

        from ichrisbirch.schemas.backup import BackupCreate

        with pytest.raises(ValidationError):
            BackupCreate(description='!@#$%')


class TestBackupEndpointResponses:
    """Test backup endpoint response handling.

    These tests mock DatabaseBackup to verify the API layer correctly:
    - Returns 201 on success
    - Returns 500 on backup failure
    - Includes all expected fields in response
    """

    def test_create_backup_returns_201_on_success(self, test_api_logged_in_admin):
        """POST /admin/backups/ returns 201 with backup record on success."""
        mock_record = make_backup_record(
            filename='backup-2026-01-15T1200-api-test.dump',
            description='api-test',
        )

        with patch('ichrisbirch.api.endpoints.admin.DatabaseBackup') as mock_class:
            mock_class.return_value.backup.return_value = mock_record

            response = test_api_logged_in_admin.post(
                ENDPOINT,
                json={'description': 'api-test', 'upload_to_s3': False, 'save_local': True},
            )

        assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
        data = response.json()
        assert data['success'] is True
        assert data['filename'] == 'backup-2026-01-15T1200-api-test.dump'

    def test_create_backup_returns_500_on_failure(self, test_api_logged_in_admin):
        """POST /admin/backups/ returns 500 when backup fails."""
        mock_record = make_backup_record(
            success=False,
            error_message='Connection refused',
        )

        with patch('ichrisbirch.api.endpoints.admin.DatabaseBackup') as mock_class:
            mock_class.return_value.backup.return_value = mock_record

            response = test_api_logged_in_admin.post(
                ENDPOINT,
                json={'description': 'fail-test', 'upload_to_s3': False, 'save_local': True},
            )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'Connection refused' in response.json()['detail']

    def test_create_backup_response_includes_metadata(self, test_api_logged_in_admin):
        """Response includes all expected metadata fields."""
        mock_record = make_backup_record(
            postgres_version='PostgreSQL 16.11 on x86_64-pc-linux-musl, compiled by gcc (Alpine 14.2.0) 14.2.0, 64-bit',
        )

        with patch('ichrisbirch.api.endpoints.admin.DatabaseBackup') as mock_class:
            mock_class.return_value.backup.return_value = mock_record

            response = test_api_logged_in_admin.post(
                ENDPOINT,
                json={'description': 'metadata-test', 'upload_to_s3': False, 'save_local': True},
            )

        assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
        data = response.json()

        # Verify all metadata fields are present
        assert 'filename' in data
        assert 'size_bytes' in data
        assert 'checksum' in data
        assert 'duration_seconds' in data
        assert 'postgres_version' in data
        assert 'table_snapshot' in data

    def test_create_backup_passes_correct_args_to_database_backup(self, test_api_logged_in_admin):
        """Verify endpoint passes correct arguments to DatabaseBackup."""
        mock_record = make_backup_record()

        with patch('ichrisbirch.api.endpoints.admin.DatabaseBackup') as mock_class:
            mock_class.return_value.backup.return_value = mock_record

            test_api_logged_in_admin.post(
                ENDPOINT,
                json={'description': 'Args Test!', 'upload_to_s3': True, 'save_local': False},
            )

            # Verify backup was called with correct args
            mock_class.return_value.backup.assert_called_once()
            call_kwargs = mock_class.return_value.backup.call_args.kwargs
            assert call_kwargs['description'] == 'args-test'  # Sanitized
            assert call_kwargs['upload'] is True
            assert call_kwargs['save_local'] is False
            assert call_kwargs['backup_type'] == 'manual'
            assert call_kwargs['user_id'] is not None  # Admin user ID
