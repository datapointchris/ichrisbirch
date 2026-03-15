"""Tests for admin scheduler API endpoints.

These tests verify scheduler job listing, pause/resume/delete actions,
and run history retrieval. The jobstore is mocked to isolate the API layer.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import pendulum
from fastapi import status

from tests.util import show_status_and_response

SCHEDULER_ENDPOINT = '/admin/scheduler/jobs/'
HISTORY_ENDPOINT = '/admin/scheduler/history/'


def make_mock_job(job_id='test_job', name='test_job', next_run_time=None, trigger_str='cron[day="*", hour="1"]'):
    """Create a mock APScheduler Job object."""
    job = MagicMock()
    job.id = job_id
    job.name = name
    job.next_run_time = next_run_time
    job.trigger = MagicMock()
    job.trigger.__str__ = lambda self: trigger_str
    job.trigger.get_next_fire_time = MagicMock(return_value=pendulum.tomorrow())
    return job


class TestSchedulerJobsAuth:
    """Test scheduler endpoint authentication and authorization."""

    def test_list_jobs_requires_admin(self, test_api_logged_in):
        response = test_api_logged_in.get(SCHEDULER_ENDPOINT)
        assert response.status_code == status.HTTP_403_FORBIDDEN, show_status_and_response(response)

    def test_list_jobs_unauthenticated(self, test_api):
        response = test_api.get(SCHEDULER_ENDPOINT)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, show_status_and_response(response)


class TestSchedulerJobsList:
    """Test scheduler job listing."""

    @patch('ichrisbirch.api.endpoints.admin.get_jobstore')
    def test_list_jobs_returns_all_jobs(self, mock_get_jobstore, test_api_logged_in_admin):
        mock_jobstore = MagicMock()
        mock_jobstore.get_all_jobs.return_value = [
            make_mock_job('job_a', 'job_a', next_run_time=pendulum.tomorrow()),
            make_mock_job('job_b', 'job_b'),
        ]
        mock_get_jobstore.return_value = mock_jobstore

        response = test_api_logged_in_admin.get(SCHEDULER_ENDPOINT)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        data = response.json()
        assert len(data) == 2
        assert data[0]['id'] == 'job_a'
        assert data[0]['is_paused'] is False
        assert data[1]['id'] == 'job_b'
        assert data[1]['is_paused'] is True
        assert data[1]['time_until_next_run'] == 'Paused'

    @patch('ichrisbirch.api.endpoints.admin.get_jobstore')
    def test_list_jobs_empty(self, mock_get_jobstore, test_api_logged_in_admin):
        mock_jobstore = MagicMock()
        mock_jobstore.get_all_jobs.return_value = []
        mock_get_jobstore.return_value = mock_jobstore

        response = test_api_logged_in_admin.get(SCHEDULER_ENDPOINT)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json() == []


class TestSchedulerJobPause:
    """Test pausing scheduler jobs."""

    @patch('ichrisbirch.api.endpoints.admin.get_jobstore')
    def test_pause_job(self, mock_get_jobstore, test_api_logged_in_admin):
        mock_job = make_mock_job('daily_task', 'daily_task', next_run_time=pendulum.tomorrow())
        mock_jobstore = MagicMock()
        mock_jobstore.lookup_job.return_value = mock_job
        mock_get_jobstore.return_value = mock_jobstore

        response = test_api_logged_in_admin.post(f'{SCHEDULER_ENDPOINT}daily_task/pause/')
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        data = response.json()
        assert data['is_paused'] is True
        assert data['time_until_next_run'] == 'Paused'
        mock_jobstore.update_job.assert_called_once()

    @patch('ichrisbirch.api.endpoints.admin.get_jobstore')
    def test_pause_nonexistent_job(self, mock_get_jobstore, test_api_logged_in_admin):
        mock_jobstore = MagicMock()
        mock_jobstore.lookup_job.return_value = None
        mock_get_jobstore.return_value = mock_jobstore

        response = test_api_logged_in_admin.post(f'{SCHEDULER_ENDPOINT}nonexistent/pause/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)


class TestSchedulerJobResume:
    """Test resuming scheduler jobs."""

    @patch('ichrisbirch.api.endpoints.admin.get_jobstore')
    def test_resume_job(self, mock_get_jobstore, test_api_logged_in_admin):
        mock_job = make_mock_job('paused_task', 'paused_task')
        mock_jobstore = MagicMock()
        mock_jobstore.lookup_job.return_value = mock_job
        mock_get_jobstore.return_value = mock_jobstore

        response = test_api_logged_in_admin.post(f'{SCHEDULER_ENDPOINT}paused_task/resume/')
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        data = response.json()
        assert data['is_paused'] is False
        mock_jobstore.update_job.assert_called_once()

    @patch('ichrisbirch.api.endpoints.admin.get_jobstore')
    def test_resume_nonexistent_job(self, mock_get_jobstore, test_api_logged_in_admin):
        mock_jobstore = MagicMock()
        mock_jobstore.lookup_job.return_value = None
        mock_get_jobstore.return_value = mock_jobstore

        response = test_api_logged_in_admin.post(f'{SCHEDULER_ENDPOINT}nonexistent/resume/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)


class TestSchedulerJobDelete:
    """Test deleting scheduler jobs."""

    @patch('ichrisbirch.api.endpoints.admin.get_jobstore')
    def test_delete_job(self, mock_get_jobstore, test_api_logged_in_admin):
        mock_job = make_mock_job('temp_job', 'temp_job')
        mock_jobstore = MagicMock()
        mock_jobstore.lookup_job.return_value = mock_job
        mock_get_jobstore.return_value = mock_jobstore

        response = test_api_logged_in_admin.delete(f'{SCHEDULER_ENDPOINT}temp_job/')
        assert response.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(response)
        mock_jobstore.remove_job.assert_called_once_with('temp_job')

    @patch('ichrisbirch.api.endpoints.admin.get_jobstore')
    def test_delete_nonexistent_job(self, mock_get_jobstore, test_api_logged_in_admin):
        mock_jobstore = MagicMock()
        mock_jobstore.lookup_job.return_value = None
        mock_get_jobstore.return_value = mock_jobstore

        response = test_api_logged_in_admin.delete(f'{SCHEDULER_ENDPOINT}nonexistent/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)


class TestSchedulerHistory:
    """Test scheduler run history endpoint."""

    def test_history_requires_admin(self, test_api_logged_in):
        response = test_api_logged_in.get(HISTORY_ENDPOINT)
        assert response.status_code == status.HTTP_403_FORBIDDEN, show_status_and_response(response)

    def test_history_returns_empty_list(self, test_api_logged_in_admin):
        """Fresh database should have no run history."""
        response = test_api_logged_in_admin.get(HISTORY_ENDPOINT)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json() == []

    def test_history_with_job_id_filter(self, test_api_logged_in_admin):
        """Filtering by nonexistent job_id returns empty list."""
        response = test_api_logged_in_admin.get(f'{HISTORY_ENDPOINT}?job_id=nonexistent')
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json() == []
