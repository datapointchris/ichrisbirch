import pytest
from fastapi import status

from ichrisbirch.scheduler.main import get_jobstore
from tests.test_data import scheduler
from tests.util import show_status_and_response
from tests.utils.database import test_settings

test_job_ids = [job.id for job in scheduler.BASE_DATA]


def test_index(test_app_logged_in_admin):
    response = test_app_logged_in_admin.get('/admin/scheduler/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>Scheduler</title>' in response.data


@pytest.mark.parametrize('job_id', test_job_ids)
def test_pause_and_resume_job(insert_test_jobs, test_app_logged_in_admin, job_id):
    jobstore = get_jobstore(test_settings)
    pause_response = test_app_logged_in_admin.post('/admin/scheduler/', data={'job_id': job_id, 'action': 'pause_job'})
    assert pause_response.status_code == status.HTTP_200_OK, show_status_and_response(pause_response)
    job = jobstore.lookup_job(job_id)
    assert job is not None, f'Job {job_id} should exist in the jobstore'
    assert job.next_run_time is None, f'Job {job_id} should be paused, next_run_time should be None'

    resume_response = test_app_logged_in_admin.post('/admin/scheduler/', data={'job_id': job_id, 'action': 'resume_job'})

    assert resume_response.status_code == status.HTTP_200_OK, show_status_and_response(resume_response)
    job = jobstore.lookup_job(job_id)
    assert job is not None, f'Job {job_id} should exist in the jobstore after resuming'
    assert job.next_run_time is not None, f'Job {job_id} should be resumed, next_run_time should not be None'


@pytest.mark.parametrize('job_id', test_job_ids)
def test_delete_job(insert_test_jobs, test_app_logged_in_admin, job_id):
    jobstore = get_jobstore(test_settings)
    response = test_app_logged_in_admin.post('/admin/scheduler/', data={'job_id': job_id, 'action': 'delete_job'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert jobstore.lookup_job(job_id) is None
