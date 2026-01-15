"""Tests for admin backup API endpoints."""

import pytest
from fastapi import status

from tests.util import show_status_and_response

ENDPOINT = '/admin/backups/'


class TestBackupEndpoints:
    """Test backup API endpoints."""

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


class TestBackupSchemaValidation:
    """Test backup schema validation."""

    def test_description_sanitization(self):
        """Test that description is sanitized correctly."""
        from ichrisbirch.schemas.backup import BackupCreate

        # Test normal description
        backup = BackupCreate(description='Pre Migration')
        assert backup.description == 'pre-migration'

        # Test with special characters
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
