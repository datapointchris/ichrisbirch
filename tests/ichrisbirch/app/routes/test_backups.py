"""Tests for Flask admin backup routes."""

import boto3
import pytest
from fastapi import status
from moto import mock_aws

from ichrisbirch.config import get_settings
from tests.util import show_status_and_response


@pytest.fixture
def mock_s3():
    """Mock S3 for backup tests."""
    with mock_aws():
        s3 = boto3.client('s3', region_name='us-east-1')
        settings = get_settings()
        bucket_name = settings.aws.s3_backup_bucket

        # Create the bucket
        s3.create_bucket(Bucket=bucket_name)

        # Add some test objects to simulate existing backups
        s3.put_object(
            Bucket=bucket_name,
            Key='testing/postgres/backup-2026-01-01T1200-test.dump',
            Body=b'test backup content',
        )

        yield s3


class TestBackupRoutes:
    """Test Flask admin backup routes.

    Uses function-scoped fixtures and moto for S3 mocking.
    """

    def test_get_backups(self, test_app_logged_in_admin_function, mock_s3):
        """GET /admin/backups/ displays S3 bucket contents."""
        response = test_app_logged_in_admin_function.get('/admin/backups/')
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)

    def test_get_backups_requires_admin(self, test_app_logged_in_function, mock_s3):
        """Non-admin users cannot access backups page."""
        response = test_app_logged_in_function.get('/admin/backups/')
        assert response.status_code in (status.HTTP_302_FOUND, status.HTTP_403_FORBIDDEN)

    def test_get_backups_navigates_folders(self, test_app_logged_in_admin_function, mock_s3):
        """Prefix navigation via query parameter works correctly."""
        response = test_app_logged_in_admin_function.get('/admin/backups/?prefix=testing/')
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)

    def test_post_backup_validation_no_description(self, test_app_logged_in_admin_function, mock_s3):
        """Validation error shown for missing description."""
        response = test_app_logged_in_admin_function.post(
            '/admin/backups/',
            data={'description': '', 'upload_to_s3': 'on'},
            follow_redirects=True,
        )
        assert response.status_code == status.HTTP_200_OK
        assert b'Description is required' in response.data or b'error' in response.data.lower()

    def test_post_backup_validation_no_destination(self, test_app_logged_in_admin_function, mock_s3):
        """Validation error shown when no destination selected."""
        response = test_app_logged_in_admin_function.post(
            '/admin/backups/',
            data={'description': 'test-backup'},
            follow_redirects=True,
        )
        assert response.status_code == status.HTTP_200_OK
        assert b'Select at least one destination' in response.data or b'error' in response.data.lower()

    def test_post_backup_creates_backup(self, test_app_logged_in_admin_function, mock_s3):
        """POST /admin/backups/ creates backup successfully."""
        response = test_app_logged_in_admin_function.post(
            '/admin/backups/',
            data={
                'description': 'flask-integration-test',
                'save_local': 'on',
            },
            follow_redirects=True,
        )
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert b'Backup created' in response.data

    def test_post_backup_shows_filename_in_flash(self, test_app_logged_in_admin_function, mock_s3):
        """Success flash message includes backup filename."""
        response = test_app_logged_in_admin_function.post(
            '/admin/backups/',
            data={
                'description': 'filename-test',
                'save_local': 'on',
            },
            follow_redirects=True,
        )
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert b'backup-' in response.data
        assert b'filename-test' in response.data
